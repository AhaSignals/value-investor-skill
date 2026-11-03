import copy
import importlib.util
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.research import ResearchError, analyze, digest, html_report, timestamp, validate
from core.ledger import connect, diff, freeze, records, revise, unpack, update_evidence, verify


def fixture(name="clinical"):
    return json.loads((ROOT / "examples" / (name + ".json")).read_text(encoding="utf-8"))


class ArithmeticTests(unittest.TestCase):
    def test_independent_pair_arithmetic(self):
        r = analyze(fixture())
        pairs = {(x["low"], x["high"]): x for x in r["pairwise_price_weights"]}
        self.assertAlmostEqual(pairs["unfavorable", "favorable80"]["high_weight"], 1 / 3)
        self.assertAlmostEqual(pairs["unfavorable", "favorable60"]["high_weight"], .5)
        self.assertEqual(pairs["favorable60", "favorable80"]["status"], "OUTSIDE_PAIR")

    def test_merger_price_is_not_probability(self):
        r = analyze(fixture("merger"))
        feasible = sorted(x["high_weight"] for x in r["pairwise_price_weights"] if x["high_weight"] is not None)
        self.assertEqual(feasible, [.6, .8])
        self.assertEqual(r["probability_status"], "NOT_ESTIMATED")
        self.assertEqual(r["decision_status"], "NO_QUOTE")

    def test_cash_debt_costs_and_dilution(self):
        b = fixture()
        b["scenarios"][0].update(operating_value_pv=600, cash=100, debt=50, other_claims=10,
                                  new_capital_net=80, future_costs_pv=20, shares=100, new_shares=40)
        self.assertEqual(analyze(b)["scenarios"][0]["per_share"], 5)

    def test_market_price_cannot_change_state_values(self):
        b = fixture()
        first = analyze(b)
        b["price"]["value"] = 45
        second = analyze(b)
        self.assertEqual(first["scenarios"], second["scenarios"])
        self.assertNotEqual(first["pairwise_price_weights"], second["pairwise_price_weights"])

    def test_negative_equity_floor_is_visible(self):
        b = fixture(); b["scenarios"][0]["debt"] = 10_000_000_000
        s = analyze(b)["scenarios"][0]
        self.assertTrue(s["equity_floor_applied"])
        self.assertEqual(s["per_share"], 0)

    def test_equal_values_do_not_divide_by_zero(self):
        b = fixture()
        for s in b["scenarios"]:
            s["operating_value_pv"] = 4_000_000_000
        self.assertEqual(analyze(b)["pairwise_price_weights"], [])

    def test_weights_never_upgrade_authority(self):
        b = fixture(); b["scenario_weights"] = {"favorable80": .25, "favorable60": .25, "unfavorable": .5}
        b["weight_basis"] = "Illustrative assumed weights"
        r = analyze(b)
        self.assertEqual(r["weighted_scenario_value"], 45)
        self.assertEqual(r["probability_status"], "NOT_ESTIMATED")


class ValidationTests(unittest.TestCase):
    def test_numeric_overflow_rejected(self):
        b = fixture(); b["scenarios"][0].update(operating_value_pv=1e308, cash=1e308)
        with self.assertRaises(ResearchError): analyze(b)
        b = fixture(); b["scenarios"][0]["shares"] = 10 ** 1000
        with self.assertRaises(ResearchError): analyze(b)

    def test_publication_cutoff_abstains(self):
        b = fixture(); b["evidence"][0].update(published_at="2026-11-03T00:00:00Z", observed_at="2026-11-03T00:01:00Z")
        r = analyze(b)
        self.assertIsNone(r["scenarios"][0]["per_share"])
        self.assertEqual(r["scenarios"][2]["per_share"], 20)

    def test_observation_and_publication_are_distinct(self):
        b = fixture(); b["evidence"][0]["observed_at"] = "2026-11-03T00:00:00Z"
        self.assertEqual(analyze(b)["status"], "NEEDS_REVIEW")
        b["mode"] = "historical_public"
        self.assertEqual(analyze(b)["status"], "SCENARIO_ONLY")

    def test_withdrawn_dependency_abstains(self):
        b = fixture(); b["evidence"][0]["status"] = "withdrawn"
        r = analyze(b)
        self.assertIsNone(r["scenarios"][0]["per_share"])
        self.assertEqual(r["pairwise_price_weights"], [])

    def test_stale_and_future_prices_withhold_comparison(self):
        for value in ("2026-11-01T16:00:00Z", "2026-11-03T16:00:00Z"):
            b = fixture(); b["price"]["as_of"] = value
            self.assertEqual(analyze(b)["pairwise_price_weights"], [])
            self.assertEqual(analyze(b)["scenarios"][0]["per_share"], 80)

    def test_nonfinite_bool_and_negative_shares_rejected(self):
        for bad in (float("nan"), float("inf"), True, -1, 0, "100"):
            b = fixture(); b["scenarios"][0]["shares"] = bad
            with self.assertRaises(ResearchError): analyze(b)

    def test_unknown_and_duplicate_evidence_rejected(self):
        b = fixture(); b["scenarios"][0]["evidence_ids"] = ["missing"]
        with self.assertRaises(ResearchError): analyze(b)
        b = fixture(); b["evidence"].append(copy.deepcopy(b["evidence"][0]))
        with self.assertRaises(ResearchError): analyze(b)

    def test_naive_time_and_bad_weights_rejected(self):
        b = fixture(); b["cutoff"] = "2026-11-02T16:00:00"
        with self.assertRaises(ResearchError): analyze(b)
        b = fixture(); b["scenario_weights"] = {"favorable80": .5}
        with self.assertRaises(ResearchError): analyze(b)

    def test_observed_before_published_rejected(self):
        b = fixture(); b["evidence"][0]["observed_at"] = "2020-01-01T00:00:00Z"
        with self.assertRaises(ResearchError): analyze(b)

    def test_real_bundle_requires_sources(self):
        b = fixture(); b["fictional"] = False; b["evidence"][0]["url"] = "javascript:alert(1)"
        with self.assertRaises(ResearchError): analyze(b)

    def test_html_input_cannot_execute(self):
        b = fixture(); b["company"] = '<script>alert("x")</script>'
        output = html_report(b, analyze(b))
        self.assertNotIn('<script>', output)
        self.assertIn('alert', output)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / "ledger.sqlite")
        self.bundle = fixture()
        self.first = freeze(self.db, self.bundle)

    def tearDown(self):
        self.db.close(); self.temp.cleanup()

    def test_freeze_is_idempotent_and_refuses_overwrite(self):
        self.assertEqual(freeze(self.db, self.bundle)["hash"], self.first["hash"])
        b = fixture(); b["price"]["value"] = 42
        with self.assertRaises(ResearchError): freeze(self.db, b)
        self.assertEqual(len(records(self.db, b["id"])), 1)

    def test_evidence_update_preserves_history_and_is_idempotent(self):
        e = fixture("withdrawal")
        second = update_evidence(self.db, self.bundle["id"], e, 1)
        self.assertEqual(second["analysis"]["status"], "NEEDS_REVIEW")
        self.assertEqual(unpack(records(self.db, self.bundle["id"])[0])["analysis"]["scenarios"][0]["per_share"], 80)
        self.assertEqual(update_evidence(self.db, self.bundle["id"], e, 1)["hash"], second["hash"])
        self.assertEqual(verify(self.db)["snapshots"], 2)

    def test_reused_event_id_with_different_content_rejected(self):
        e = fixture("withdrawal"); update_evidence(self.db, self.bundle["id"], e, 1)
        e["reason"] = "different"
        with self.assertRaises(ResearchError): update_evidence(self.db, self.bundle["id"], e, 2)

    def test_version_conflict_rolls_back(self):
        e = fixture("withdrawal")
        with self.assertRaises(ResearchError): update_evidence(self.db, self.bundle["id"], e, 9)
        self.assertEqual(verify(self.db)["snapshots"], 1)

    def test_evidence_hash_conflict_rolls_back(self):
        e = fixture("withdrawal"); e["expected_evidence_hash"] = "wrong"
        with self.assertRaises(ResearchError): update_evidence(self.db, self.bundle["id"], e, 1)
        self.assertEqual(verify(self.db)["snapshots"], 1)

    def test_active_source_needs_full_review(self):
        e = fixture("withdrawal"); e["replacement"]["status"] = "active"
        with self.assertRaises(ResearchError): update_evidence(self.db, self.bundle["id"], e, 1)

    def test_full_revision_is_new_and_price_blind(self):
        b = fixture(); b["price"]["value"] = 45
        second = revise(self.db, b, 1, "New price snapshot")
        self.assertEqual(second["version"], 2)
        self.assertEqual(second["analysis"]["scenarios"], self.first["analysis"]["scenarios"])
        self.assertTrue(diff(self.bundle, b))

    def test_backward_cutoff_rejected(self):
        b = fixture(); b["cutoff"] = "2026-11-01T15:00:00Z"
        with self.assertRaises(ResearchError): revise(self.db, b, 1, "Invalid history")

    def test_app_level_mutations_blocked(self):
        for sql in ("UPDATE snapshots SET hash='bad'", "DELETE FROM snapshots"):
            with self.assertRaises(sqlite3.IntegrityError): self.db.execute(sql)
        self.db.rollback()
        self.assertEqual(verify(self.db)["snapshots"], 1)

    def test_tampering_detected(self):
        self.db.execute("DROP TRIGGER no_update")
        self.db.execute("UPDATE snapshots SET payload='{}'")
        self.db.commit()
        with self.assertRaises(ResearchError): verify(self.db)

    def test_restart_reproduces_history(self):
        path = Path(self.temp.name) / "ledger.sqlite"
        self.db.close(); self.db = connect(path)
        self.assertEqual(verify(self.db)["snapshots"], 1)


class IntegrationTests(unittest.TestCase):
    def test_demo_and_existing_ledger_protection(self):
        with tempfile.TemporaryDirectory() as temp:
            cmd = [sys.executable, str(ROOT / "scripts/investor.py"), "demo", "--out", temp]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result["after"], "NEEDS_REVIEW")
            self.assertTrue((Path(temp) / "after/research.html").is_file())
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)

    def test_installed_copy_runs_without_original_workdir(self):
        with tempfile.TemporaryDirectory() as temp:
            cmd = [sys.executable, str(ROOT / "scripts/install.py"), "--target", temp]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
            install = Path(temp) / "value-investor-skill"
            run = subprocess.run([sys.executable, str(install / "scripts/investor.py"), "demo", "--out", str(Path(temp) / "demo")], cwd=temp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_invalid_json_returns_clean_error(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "bad.json"; p.write_text("{")
            run = subprocess.run([sys.executable, str(ROOT / "scripts/investor.py"), "analyze", str(p)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn("Traceback", run.stderr)

    def test_sec_acceptance_time_not_fiscal_period(self):
        spec = importlib.util.spec_from_file_location("sec", ROOT / "scripts/fetch_sec.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        data = {"filings": {"recent": {"accessionNumber": ["0000000001-26-000001", "0000000001-26-000002"], "acceptanceDateTime": ["2026-10-01T00:00:00Z", "2026-11-03T00:00:00Z"], "form": ["10-Q", "10-Q/A"], "primaryDocument": ["a.htm", "b.htm"]}}}
        rows = mod.select_filings(data, timestamp("2026-11-02T00:00:00Z"), "1")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["form"], "10-Q")
        data["filings"]["recent"]["primaryDocument"][0] = "xslF345X06/form4.xml"
        rows = mod.select_filings(data, timestamp("2026-11-02T00:00:00Z"), "1")
        self.assertTrue(rows[0]["url"].endswith("/xslF345X06/form4.xml"))
        data["filings"]["recent"]["primaryDocument"][0] = "../secret.xml"
        with self.assertRaises(ResearchError):
            mod.select_filings(data, timestamp("2026-11-02T00:00:00Z"), "1")


if __name__ == "__main__":
    unittest.main()
