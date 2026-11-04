import copy
import http.client
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from core.desk import DeskServer, examples
from core.research import ResearchError
from core.valuation import calculate, pit_check, review_forecasts


def scenario(**changes):
    return dict({'method':'equity_dcf','cash_per_share':10,'price':100,'required_return':.1,'growth':0,
                 'terminal_growth':0,'dilution':0,'years':5,'reviewed':True,
                 'rationale':'Illustrative equity cash after all reinvestment and financing needs.'},**changes)


class ValuationTests(unittest.TestCase):
    def test_constant_cash_equals_perpetuity_and_reverse_zero(self):
        result=calculate(scenario())
        self.assertAlmostEqual(result['value_per_share'],100)
        self.assertAlmostEqual(result['price_required_growth'],0)
        self.assertAlmostEqual(result['projection'][0]['present_value'],10/1.1)
        self.assertGreater(result['sensitivity'][0]['value_per_share'],result['sensitivity'][-1]['value_per_share'])

    def test_dilution_reduces_each_share_value_and_growth_is_total_cash(self):
        result=calculate(scenario(dilution=.05,growth=.05))
        self.assertAlmostEqual(result['projection'][0]['cash_per_share'],10)
        self.assertLess(result['value_per_share'],100)

    def test_price_does_not_change_scenario_economics(self):
        one,two=calculate(scenario()),calculate(scenario(price=200))
        self.assertEqual(one['value_per_share'],two['value_per_share'])
        self.assertNotEqual(one['price_required_growth'],two['price_required_growth'])

    def test_epv_and_residual_income_use_equity_basis(self):
        self.assertEqual(calculate(scenario(method='earnings_power'))['value_per_share'],100)
        r=calculate(scenario(method='residual_income',book_per_share=50,roe=.1,payout=.5))
        self.assertEqual(r['value_per_share'],50)
        r=calculate(scenario(method='residual_income',book_per_share=50,roe=.12,payout=1))
        self.assertAlmostEqual(r['value_per_share'],50+sum(1/1.1**y for y in range(1,6)))

    def test_invalid_assumptions_and_terminal_singularity_fail(self):
        for change in [dict(price=10**1000),dict(extra=float('inf')),dict(price=True),dict(price=float('nan')),dict(cash_per_share=-1),dict(years=2.5),dict(terminal_growth=.1),dict(reviewed=False),dict(rationale='yes'),dict(dilution=-.1)]:
            with self.subTest(change=change),self.assertRaises(ResearchError): calculate(scenario(**change))

    def test_extreme_price_is_not_clipped_to_a_growth_forecast(self):
        self.assertIsNone(calculate(scenario(price=1e9))['price_required_growth'])

    def test_bank_assumptions_cannot_be_hidden_as_automatic_equity_cash(self):
        with self.assertRaises(ResearchError): calculate(scenario(method='residual_income'))

    def test_inputs_not_mutated(self):
        x=scenario();before=copy.deepcopy(x);calculate(x);self.assertEqual(x,before)

    def test_pit_missing_dependency_is_unknown(self):
        with patch.dict(sys.modules,{'ahasignals_pit':None}): self.assertEqual(pit_check({})['gate'],'UNKNOWN')

    def test_forecast_requires_freeze_before_period_and_preserves_zero_actual(self):
        row=dict(metric='cash_after_capex',unit='USD',forecast=10,actual=0,source='https://www.sec.gov/',
                 frozen_at='2024-01-01T00:00:00Z',period_end='2024-12-31T00:00:00Z',actual_available_at='2025-02-01T00:00:00Z')
        r=review_forecasts({'rows':[row]});self.assertIsNone(r['rows'][0]['absolute_percentage_error'])
        row['frozen_at']='2025-01-01T00:00:00Z'
        with self.assertRaises(ResearchError):review_forecasts({'rows':[row]})

    def test_malformed_forecast_has_actionable_error(self):
        for row in [None, {}, {'metric':'cash','unit':'USD','source':'filing','forecast':10,'actual':9}]:
            with self.assertRaises(ResearchError): review_forecasts({'rows':[row]})

    def test_forecast_overflow_and_nonfinite_metadata_fail_cleanly(self):
        row=dict(metric='cash',unit='USD',forecast=1e308,actual=-1e308,source='filing',
                 frozen_at='2024-01-01T00:00:00Z',period_end='2024-12-31T00:00:00Z',actual_available_at='2025-02-01T00:00:00Z')
        with self.assertRaises(ResearchError): review_forecasts({'rows':[row]})
        row.update(forecast=10,actual=9,extra=float('nan'))
        with self.assertRaises(ResearchError): review_forecasts({'rows':[row]})

    def test_three_real_financial_examples_are_reproducible(self):
        self.assertEqual({x['ticker'] for x in examples()},{'MSFT','KO','CAT'})
        from core.scanner import scan
        root=Path(__file__).resolve().parents[1]
        for ticker,date in [('msft','2026-11-04'),('ko','2026-11-05'),('cat','2026-11-05')]:
            b=json.loads((root/'examples'/f'{ticker}-financials-{date}.json').read_text())
            self.assertFalse(b['fictional']);self.assertFalse(b['bars']);self.assertFalse(b['valuations']);scan(b)


class DeskHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.server=DeskServer(('127.0.0.1',0),self.temp.name)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()

    def request(self,path='/',method='GET',body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        conn.request(method,path,body,headers or {});r=conn.getresponse();data=r.read();conn.close();return r.status,data,r.headers

    def test_no_network_for_examples_and_content_security(self):
        with patch('core.us_research.collect',side_effect=AssertionError('network called')):
            status,body,h=self.request('/api/session');self.assertEqual(status,200)
            self.assertEqual(len(json.loads(body)['cases']),3)
            self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy'])

    def test_cross_origin_and_dns_rebinding_rejected(self):
        for headers in [{'Host':'evil.example'},{'Origin':'https://evil.example'},{'Sec-Fetch-Site':'cross-site'}]:
            self.assertEqual(self.request('/api/session',headers=headers)[0],403)

    def test_mutations_require_token_and_json(self):
        raw=json.dumps(scenario())
        self.assertEqual(self.request('/api/value','POST',raw,{'Content-Type':'application/json'})[0],403)
        h={'Content-Type':'application/json','X-Desk-Token':self.server.token}
        self.assertEqual(self.request('/api/value','POST',raw,h)[0],200)
        # Reject the declared oversized body before a client uploads it.
        self.assertEqual(self.request('/api/value','POST',b'',dict(h, **{'Content-Length':'1000001'}))[0],413)
        self.assertEqual(self.request('/api/value','POST','{}',h)[0],400)

    def test_private_sources_and_arbitrary_files_not_served(self):
        for p in ['/../LICENSE','/reports/x/sources/facts.json','/assets/../../LICENSE','/api/jobs/unknown']:
            self.assertEqual(self.request(p)[0],404)

    def test_capture_errors_are_visible_and_no_arbitrary_command_runs(self):
        with patch('core.us_research.collect',side_effect=ResearchError('Provider returned HTTP 429')):
            job=self.server.start_research('MSFT')['job']
            for _ in range(100):
                if self.server.jobs[job]['state']!='running':break
                threading.Event().wait(.01)
            self.assertEqual(self.server.jobs[job]['state'],'error')
            self.assertIn('429',self.server.jobs[job]['error'])
        with self.assertRaises(ResearchError):self.server.start_research('MSFT\ncommand')

    def test_duplicate_inflight_and_session_limit(self):
        self.server.jobs['pending']={'state':'running'}
        with self.assertRaises(ResearchError):self.server.start_research('KO')


if __name__=='__main__':unittest.main()
