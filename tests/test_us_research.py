import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from core.research import ResearchError, timestamp
from core.scanner import scan
from core.us_research import (Capture, resolve_company, annual_financials, ttm_eps, chart_rows,
                              filing_excerpts, build_bundle, replay, collect, us_session_times)

UTC = timezone.utc
CIK = '0000000123'
ACC = '0000000123-25-000001'
ISSUER = {'ticker':'TEST','name':'Test Manufacturing Inc','cik':CIK}


def fact(value, start='2024-01-01', end='2024-12-31', filed='2025-02-01', accn=ACC, form='10-K'):
    r = {'val':value,'end':end,'filed':filed,'accn':accn,'form':form}
    if start is not None: r['start']=start
    return r


def fixtures():
    mapping = {'RevenueFromContractWithCustomerExcludingAssessedTax':100,'NetIncomeLoss':20,
               'NetCashProvidedByUsedInOperatingActivities':25,'PaymentsToAcquirePropertyPlantAndEquipment':7,
               'CashAndCashEquivalentsAtCarryingValue':30,'WeightedAverageNumberOfDilutedSharesOutstanding':10,
               'LongTermDebt':40,'LongTermDebtCurrent':10,'LongTermDebtNoncurrent':30,'ShortTermBorrowings':5,
               'EarningsPerShareDiluted':2}
    gaap={}
    for tag,val in mapping.items():
        unit='shares' if tag.startswith('Weighted') else 'USD/shares' if tag.startswith('Earnings') else 'USD'
        start=None if tag.startswith(('Cash','LongTerm','ShortTerm')) else '2024-01-01'
        gaap[tag]={'units':{unit:[fact(val,start=start)]}}
    facts={'cik':123,'entityName':ISSUER['name'],'facts':{'us-gaap':gaap}}
    directory={'0':{'ticker':'TEST','title':ISSUER['name'],'cik_str':123}}
    submissions={'cik':'123','name':ISSUER['name'],'sic':'3571','sicDescription':'Manufacturing','tickers':['TEST'],
                 'filings':{'recent':{'accessionNumber':[ACC],'form':['10-K'],'filingDate':['2025-02-01'],
                 'acceptanceDateTime':['2025-02-01T21:00:00Z'],'primaryDocument':['annual.htm'],'reportDate':['2024-12-31']}}}
    price={'chart':{'result':[{'meta':{'currency':'USD','instrumentType':'EQUITY','symbol':'TEST','exchangeTimezoneName':'America/New_York'},
            'timestamp':[int(timestamp('2025-02-28T14:30:00Z').timestamp())],
            'indicators':{'quote':[{'open':[10],'high':[12],'low':[9],'close':[11]}]}}],'error':None}}
    raw={'directory':directory,'facts':facts,'submissions':submissions,'prices':price}
    urls={'directory':'https://www.sec.gov/files/company_tickers.json','facts':'https://data.sec.gov/api/xbrl/companyfacts/CIK0000000123.json',
          'submissions':'https://data.sec.gov/submissions/CIK0000000123.json','prices':'https://query1.finance.yahoo.com/v8/finance/chart/TEST'}
    entries=[{'role':k,'file':k+'.json','url':urls[k],'observed_at':'2025-03-01T00:00:00Z','sha256':hashlib.sha256(json.dumps(v).encode()).hexdigest()} for k,v in raw.items()]
    manifest={'capture_version':1,'issuer':ISSUER,'cutoff':'2025-03-01T01:00:00Z','sources':entries,'errors':[]}
    return raw,manifest


class USResearchTests(unittest.TestCase):
    def test_resolver_name_symbol_class_and_ambiguity(self):
        directory={'a':{'ticker':'MSFT','title':'MICROSOFT CORP','cik_str':789019},
                   'b':{'ticker':'AAPL','title':'Apple Inc','cik_str':320193},
                   'c':{'ticker':'APLE','title':'Apple Hospitality REIT Inc','cik_str':1234}}
        self.assertEqual(resolve_company('Microsoft',directory)['ticker'],'MSFT')
        self.assertEqual(resolve_company('微软',directory)['ticker'],'MSFT')
        self.assertEqual(resolve_company('apple',directory)['ticker'],'AAPL')
        directory['d']={'ticker':'TEST.B','title':'MICROSOFT CORP','cik_str':123}
        with self.assertRaisesRegex(ResearchError,'Several'): resolve_company('Microsoft',directory)
        self.assertEqual(resolve_company('TEST-B',directory)['ticker'],'TEST.B')

    def test_unknown_name_stops_before_a_guessed_security(self):
        with self.assertRaisesRegex(ResearchError,'No SEC-listed match'): resolve_company('missing',fixtures()[0]['directory'])

    def test_financial_units_periods_and_debt_do_not_double_count(self):
        raw,manifest=fixtures()
        bundle,_=build_bundle(raw,manifest)
        row=bundle['financials'][0]
        self.assertEqual(row['debt'],45)  # 40 total long-term + 5 short-term, not 40+10+30+5.
        self.assertEqual(scan(bundle)['financials']['free_cash_flow'],18)
        self.assertEqual(len(row['field_sources']['debt']),2)

    def test_missing_debt_not_imputed_from_commercial_paper(self):
        raw,manifest=fixtures()
        gaap=raw['facts']['facts']['us-gaap']
        del gaap['ShortTermBorrowings']
        gaap['CommercialPaper']={'units':{'USD':[fact(0,start=None)]}}
        bundle,_=build_bundle(raw,manifest)
        self.assertIsNone(bundle['financials'][0]['debt'])
        self.assertIsNone(scan(bundle)['financials']['net_debt'])
        self.assertEqual(scan(bundle)['financials']['status'],'PARTIAL')

    def test_missing_capex_not_zero_and_wrong_currency_not_mixed(self):
        raw,manifest=fixtures()
        gaap=raw['facts']['facts']['us-gaap']
        gaap['PaymentsToAcquirePropertyPlantAndEquipment']['units']={'EUR':[fact(7)]}
        bundle,_=build_bundle(raw,manifest)
        self.assertIsNone(bundle['financials'][0]['capex'])
        self.assertIsNone(scan(bundle)['financials']['free_cash_flow'])

    def test_quarter_cannot_replace_full_year(self):
        raw,manifest=fixtures()
        raw['facts']['facts']['us-gaap']['NetIncomeLoss']['units']['USD']=[fact(9,start='2024-10-01')]
        with self.assertRaisesRegex(ResearchError,'No supported USD annual'): build_bundle(raw,manifest)

    def test_future_restatement_not_used_at_old_close(self):
        raw,_=fixtures()
        rows=raw['facts']['facts']['us-gaap']['EarningsPerShareDiluted']['units']['USD/shares']
        rows.append(fact(4,filed='2025-03-15',accn='0000000123-25-000002'))
        early=ttm_eps(raw['facts'],timestamp('2025-03-01T00:00:00Z'),{},[],CIK)
        later=ttm_eps(raw['facts'],timestamp('2025-03-17T00:00:00Z'),{},[],CIK)
        self.assertEqual(early['value'],2)
        self.assertEqual(later['value'],4)

    def test_ytd_bridge_is_not_sum_of_cumulative_quarters(self):
        raw,_=fixtures()
        rows=raw['facts']['facts']['us-gaap']['EarningsPerShareDiluted']['units']['USD/shares']
        rows += [fact(.8,end='2024-03-31',filed='2024-05-01',accn='0000000123-24-000001',form='10-Q'),
                 fact(1.2,start='2025-01-01',end='2025-03-31',filed='2025-05-01',accn='0000000123-25-000002',form='10-Q')]
        got=ttm_eps(raw['facts'],timestamp('2025-05-03T00:00:00Z'),{},[],CIK)
        self.assertAlmostEqual(got['value'],2.4)  # 2 + 1.2 - .8
        self.assertEqual(len(got['components']),3)

    def test_eps_split_alignment_and_unfinished_session(self):
        raw,manifest=fixtures()
        got=ttm_eps(raw['facts'],timestamp('2025-03-01T00:00:00Z'),{},[(timestamp('2025-02-15T14:30:00Z'),2)],CIK)
        self.assertEqual(got['value'],1)
        data=raw['prices']['chart']['result'][0]
        data['timestamp'][0]=int(timestamp('2025-03-01T14:30:00Z').timestamp())
        rows,_,rejected=chart_rows(raw['prices'],ISSUER,timestamp(manifest['cutoff']),manifest['cutoff'])
        self.assertEqual(rows,[])
        self.assertEqual(rejected[0]['reason'],'current_or_future_UTC_date')

    def test_provider_adjusted_close_is_not_used(self):
        raw,manifest=fixtures()
        raw['prices']['chart']['result'][0]['indicators']['adjclose']=[{'adjclose':[1]}]
        rows,_,_=chart_rows(raw['prices'],ISSUER,timestamp(manifest['cutoff']),manifest['cutoff'])
        self.assertEqual(rows[0]['close'],11)

    def test_wrong_ticker_or_price_currency_does_not_corrupt_financials(self):
        raw,manifest=fixtures()
        raw['prices']['chart']['result'][0]['meta']['symbol']='OTHER'
        bundle,context=build_bundle(raw,manifest)
        self.assertEqual(bundle['bars'],[])
        self.assertTrue(context['provider_errors'])
        self.assertEqual(bundle['financials'][0]['revenue'],100)

    def test_bank_and_identity_mismatch_stop(self):
        for field,value in [('sic','6021'),('cik','456')]:
            raw,manifest=fixtures()
            raw['submissions'][field]=value
            with self.assertRaises(ResearchError): build_bundle(raw,manifest)

    def test_conflicting_contexts_are_unknown(self):
        raw,manifest=fixtures()
        raw['facts']['facts']['us-gaap']['PaymentsToAcquirePropertyPlantAndEquipment']['units']['USD'].append(fact(99))
        bundle,_=build_bundle(raw,manifest)
        self.assertIsNone(bundle['financials'][0]['capex'])

    def test_annual_excerpt_drops_scripts_and_forward_looking_boilerplate(self):
        text='<script>Our business '+('secret '*30)+'</script><p>Forward-looking statements '+('our business '*30)+'</p><p>We develop '+('software for business customers. '*10)+'</p><p>Capital expenditures '+('include data center equipment. '*10)+'</p>'
        got=filing_excerpts(text)
        self.assertEqual(len(got['business']),1)
        self.assertNotIn('secret',str(got))
        self.assertTrue(got['cash_and_investment'])

    def test_replay_exact_and_no_network_then_tamper_rejected(self):
        raw,manifest=fixtures()
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'original';(root/'sources').mkdir(parents=True)
            (root/'capture.json').write_text(json.dumps(manifest))
            for role,data in raw.items(): (root/'sources'/ (role+'.json')).write_text(json.dumps(data))
            with patch('core.us_research.urlopen',side_effect=AssertionError('No network in replay')):
                a=replay(root,Path(t)/'a');b=replay(root,Path(t)/'b')
            self.assertEqual(a,b)
            self.assertEqual((Path(t)/'a/research.html').read_bytes(),(Path(t)/'b/research.html').read_bytes())
            (root/'sources/facts.json').write_text('{}')
            with self.assertRaisesRegex(ResearchError,'integrity'): replay(root,Path(t)/'bad')

    def test_manifest_path_traversal_rejected(self):
        raw,manifest=fixtures()
        manifest['sources'][0]['file']='../secrets.json'
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'capture.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ResearchError,'Unsafe'): replay(root,root/'out')

    def test_http_429_stops_without_retry_or_header_leak(self):
        with tempfile.TemporaryDirectory() as t:
            cap=Capture(Path(t)/'sources')
            with patch('core.us_research.urlopen',side_effect=HTTPError('https://data.sec.gov',429,'limited',{},None)) as request:
                with self.assertRaisesRegex(ResearchError,'HTTP 429'): cap.get('facts','https://data.sec.gov/example.json')
            self.assertEqual(request.call_count,1)
            self.assertEqual(cap.entries,[])

    def test_live_pipeline_with_mock_sources_and_name_only(self):
        raw,_=fixtures()
        def get(cap,role,url,as_json=True):
            if role=='annual_filing':
                raise ResearchError('annual_filing provider returned HTTP 403; stopped')
            cap.entries.append({'role':role,'file':role+'.json','url':url,'observed_at':'2025-03-01T00:00:00Z','sha256':'0'*64})
            return raw[role]
        with tempfile.TemporaryDirectory() as t, patch.object(Capture,'get',get), patch('core.us_research.utc_now',return_value='2025-03-01T01:00:00Z'):
            got=collect('Test Manufacturing',Path(t)/'result')
            self.assertEqual(got['ticker'],'TEST')
            self.assertEqual(got['status'],'PARTIAL')
            self.assertTrue((Path(t)/'result/research.html').exists())

    def test_public_msft_financial_fixture_reproduces_expected_hashes(self):
        from core.research import digest
        root=Path(__file__).resolve().parents[1]
        bundle=json.loads((root/'examples/msft-financials-2026-11-04.json').read_text())
        expected=json.loads((root/'examples/msft-financials-expected.json').read_text())
        result=scan(bundle)
        self.assertEqual(digest(bundle),expected['input_sha256'])
        self.assertEqual(digest(result),expected['scan_sha256'])
        self.assertEqual(result['financials']['free_cash_flow'],expected['free_cash_flow'])
        self.assertIsNone(result['financials']['net_debt'])
        self.assertEqual(bundle['bars'],[])
        self.assertEqual(bundle['valuations'],[])

    def test_dst_open_times(self):
        self.assertEqual(us_session_times(timestamp('2025-01-15T00:00:00Z').date())[0].hour,14)
        self.assertEqual(us_session_times(timestamp('2025-07-15T00:00:00Z').date())[0].hour,13)


if __name__=='__main__': unittest.main()
