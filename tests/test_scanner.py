import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from core.scanner import scan, save, figures
from core.research import ResearchError

ROOT = Path(__file__).resolve().parents[1]


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads((ROOT / 'examples/value-trap.json').read_text())

    def test_value_trap_is_not_a_value_rating(self):
        r = scan(self.bundle)
        self.assertEqual(r['financials']['free_cash_flow'], -3000000)
        self.assertAlmostEqual(r['financials']['cash_conversion'], 1/3)
        self.assertEqual(r['financials']['net_debt'], 35000000)
        self.assertEqual(r['valuation']['current_pe'], 10)
        self.assertEqual(r['valuation']['historical_median'], 20)
        self.assertEqual(r['valuation']['percentile'], 0)
        self.assertEqual(r['status'], 'DESCRIPTIVE_ONLY')
        self.assertTrue({'PE_BELOW_HISTORY','PROFIT_WITHOUT_FREE_CASH','DILUTION','NET_DEBT_INCREASED'} <= {x['code'] for x in r['findings']})

    def test_current_observation_is_not_in_baseline(self):
        a = scan(self.bundle)
        self.bundle['valuations'][-1]['close'] *= 20
        b = scan(self.bundle)
        self.assertEqual(a['valuation']['historical_mean'], b['valuation']['historical_mean'])
        self.assertEqual(b['valuation']['percentile'], 100)

    def test_losses_do_not_become_cheap_pe(self):
        self.bundle['valuations'][-1]['eps_ttm'] = -2
        r = scan(self.bundle)
        self.assertIsNone(r['valuation']['current_pe'])
        self.assertEqual(r['valuation']['status'], 'NOT_MEANINGFUL')
        self.assertNotIn('pe-history.svg', figures(r))

    def test_loss_history_and_regime_change_withhold_baseline(self):
        for modify in ('loss','regime','gap','basis'):
            with self.subTest(modify=modify):
                b = copy.deepcopy(self.bundle)
                if modify == 'loss': b['valuations'][0]['eps_ttm'] = 0
                if modify == 'regime': b['comparable_regime'] = False
                if modify == 'gap': del b['valuations'][5]
                if modify == 'basis': b['valuations'][4]['basis'] = 'Changed accounting basis'
                self.assertIsNone(scan(b)['valuation']['historical_median'])

    def test_eps_cannot_be_backfilled_from_future(self):
        self.bundle['valuations'][0]['eps_available_at'] = '2026-11-01T12:00:00Z'
        with self.assertRaises(ResearchError): scan(self.bundle)

    def test_cutoff_and_withdrawal_exclude_data(self):
        self.bundle['financials'][-1]['status'] = 'withdrawn'
        self.bundle['valuations'][-1]['observed_at'] = '2026-12-01T12:00:00Z'
        self.bundle['bars'][-1]['available_at'] = '2026-12-01T12:00:00Z'
        self.bundle['bars'][-1]['observed_at'] = '2026-12-01T12:00:00Z'
        r = scan(self.bundle)
        self.assertEqual(len(r['excluded']), 3)
        self.assertEqual(r['financials']['free_cash_flow'], 3000000)
        self.assertEqual(r['financials']['period_end'], '2024-12-31')
        self.assertNotEqual(r['valuation']['current_pe'], 10)

    def test_empty_data_is_unknown(self):
        for k in ('financials','valuations','bars'): self.bundle[k] = []
        r = scan(self.bundle)
        for k in ('financials','valuation','price_context'):
            self.assertEqual(r[k]['status'], 'NO_DATA')

    def test_extreme_numbers_fail_without_invalid_json_or_svg(self):
        self.bundle['financials'][0]['net_income'] = 1e308
        with self.assertRaises(ResearchError): scan(self.bundle)

    def test_stale_inputs_remain_explicitly_dated(self):
        self.bundle['cutoff'] = '2030-01-01T00:00:00Z'
        r = scan(self.bundle)
        self.assertEqual(r['financials']['status'], 'STALE')
        self.assertEqual(r['valuation']['freshness'], 'STALE')
        self.assertEqual(r['price_context']['freshness'], 'STALE')

    def test_constant_price_averages_and_drawdown(self):
        for bar in self.bundle['bars']:
            bar.update(open=20,high=21,low=19,close=20)
        r = scan(self.bundle)['price_context']
        self.assertEqual(r['sma_50'],20)
        self.assertEqual(r['sma_200'],20)
        self.assertEqual(r['max_drawdown_in_window'],0)

    def test_reject_bad_units_periods_bars_and_dates(self):
        mutations = [lambda b: b.update(units='millions'),
                     lambda b: b['financials'][0].update(period_type='Q1'),
                     lambda b: b['financials'][0].update(capex=-5),
                     lambda b: b['financials'][0].update(revenue=float('nan')),
                     lambda b: b['bars'][0].update(high=1),
                     lambda b: b['bars'][0].update(close=True),
                     lambda b: b['bars'].reverse(),
                     lambda b: b['bars'].append(b['bars'][-1]),
                     lambda b: b.update(sector='bank'),
                     lambda b: b.update(price_basis='total_return'),
                     lambda b: b['financials'][0].update(observed_at='2020-01-01T00:00:00Z')]
        for m in mutations:
            b = copy.deepcopy(self.bundle)
            m(b)
            with self.assertRaises(ResearchError): scan(b)

    def test_gap_or_split_basis_suppresses_chart_stats(self):
        self.bundle['bars'][-20]['basis'] = 'unadjusted'
        r = scan(self.bundle)
        self.assertEqual(r['price_context']['status'], 'NONCOMPARABLE_HISTORY')
        self.assertIsNone(r['price_context']['sma_200'])
        self.assertNotIn('price-context.svg', figures(r))

    def test_hand_computed_price_statistics(self):
        self.bundle['bars'] = self.bundle['bars'][-3:]
        for row, c in zip(self.bundle['bars'], [10,20,15]):
            row.update(open=c,close=c,high=c+1,low=c-1)
        r = scan(self.bundle)['price_context']
        self.assertEqual(r['max_drawdown_in_window'], -.25)
        self.assertEqual(r['drawdown_from_window_high'], -.25)
        self.assertIsNone(r['sma_50'])

    def test_annual_growth_not_computed_across_missing_year(self):
        del self.bundle['financials'][1]
        self.assertIsNone(scan(self.bundle)['financials']['revenue_growth'])

    def test_real_data_requires_sources(self):
        self.bundle['fictional'] = False
        with self.assertRaises(ResearchError): scan(self.bundle)

    def test_html_escapes_imported_text_and_preserves_reports(self):
        self.bundle['company'] = '<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)/'report'
            save(out, self.bundle, scan(self.bundle))
            page = (out/'scan.html').read_text()
            self.assertNotIn('<script>', page)
            self.assertIn('&lt;script&gt;', page)
            self.assertEqual(len(list(out.glob('*.svg'))), 3)
            with self.assertRaises(ResearchError): save(out, self.bundle, scan(self.bundle))

    def test_batch_validates_every_input_before_writing(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            bad = copy.deepcopy(self.bundle)
            bad['bars'][0]['high'] = 0
            path = base/'batch.json'
            path.write_text(json.dumps([self.bundle,bad]))
            run = subprocess.run([sys.executable,str(ROOT/'scripts/investor.py'),'scan-batch',str(path),'--out',str(base/'reports')],capture_output=True)
            self.assertEqual(run.returncode,2)
            self.assertFalse((base/'reports').exists())
            path.write_text(json.dumps([self.bundle,self.bundle]))
            run = subprocess.run([sys.executable,str(ROOT/'scripts/investor.py'),'scan-batch',str(path),'--out',str(base/'reports')],capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertTrue((base/'reports/company-002/scan.html').is_file())


if __name__ == '__main__': unittest.main()
