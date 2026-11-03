#!/usr/bin/env python3
"""Value Investor Skill: local, dependency-free research CLI."""
import argparse
import copy
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.research import ResearchError, analyze, digest, html_report, markdown
from core.ledger import connect, diff, freeze, records, revise, unpack, update_evidence, verify


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def save_reports(out, bundle, result):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for filename, content in (("research.md", markdown(bundle, result)), ("research.html", html_report(bundle, result)),
                              ("analysis.json", json.dumps(result, indent=2, ensure_ascii=False)),
                              ("inputs.json", json.dumps(bundle, indent=2, ensure_ascii=False))):
        (out / filename).write_text(content, encoding="utf-8")


def demo(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    db_path = out / "research.sqlite"
    if db_path.exists():
        raise ResearchError("Demo output already contains a ledger; use a fresh directory")
    bundle = read(ROOT / "examples" / "clinical.json")
    with connect(db_path) as db:
        first = freeze(db, bundle)
        save_reports(out / "before", first["bundle"], first["analysis"])
        event = read(ROOT / "examples" / "withdrawal.json")
        event["expected_evidence_hash"] = digest(bundle["evidence"][0])
        second = update_evidence(db, bundle["id"], event, 1)
        save_reports(out / "after", second["bundle"], second["analysis"])
        changes = diff(first["bundle"], second["bundle"])
        (out / "changes.json").write_text(json.dumps(changes, indent=2), encoding="utf-8")
        status = verify(db)
    merger = read(ROOT / "examples" / "merger.json")
    save_reports(out / "merger", merger, analyze(merger))
    emit({"demo": "FICTIONAL", "before": first["analysis"]["status"], "after": second["analysis"]["status"],
          "ledger": status, "files": ["before/research.html", "after/research.html", "merger/research.html", "changes.json"]})


def main(argv=None):
    p = argparse.ArgumentParser(description="Research a stock's assumptions. No brokerage or model API calls.")
    p.add_argument("--version", action="version", version="0.1.0")
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("demo", help="Run a complete fictional before/after study")
    d.add_argument("--out", default="output/demo")
    for name in ("analyze", "freeze", "revise"):
        s = sub.add_parser(name)
        s.add_argument("bundle")
        if name == "analyze":
            s.add_argument("--out", help="Write Markdown, HTML, inputs and JSON; overwrites this report directory")
        else:
            s.add_argument("--db", required=True)
        if name == "revise":
            s.add_argument("--expected-version", type=int, required=True)
            s.add_argument("--reason", required=True)
    for name in ("history", "show", "update-evidence"):
        s = sub.add_parser(name)
        s.add_argument("study")
        s.add_argument("--db", required=True)
        if name == "show":
            s.add_argument("--study-version", type=int)
            s.add_argument("--out")
        if name == "update-evidence":
            s.add_argument("event")
            s.add_argument("--expected-version", type=int, required=True)
    s = sub.add_parser("verify")
    s.add_argument("--db", required=True)
    s = sub.add_parser("compare")
    s.add_argument("before")
    s.add_argument("after")
    a = p.parse_args(argv)
    try:
        if a.command == "demo":
            demo(a.out)
        elif a.command == "analyze":
            bundle = read(a.bundle)
            result = analyze(bundle)
            if a.out:
                save_reports(a.out, bundle, result)
            emit(result)
        elif a.command == "compare":
            emit(diff(read(a.before), read(a.after)))
        else:
            if a.command != "freeze" and not Path(a.db).is_file():
                raise ResearchError("Ledger does not exist")
            if a.command == "freeze":
                Path(a.db).parent.mkdir(parents=True, exist_ok=True)
            with connect(a.db) as db:
                if a.command == "freeze":
                    emit(freeze(db, read(a.bundle)))
                elif a.command == "revise":
                    emit(revise(db, read(a.bundle), a.expected_version, a.reason))
                elif a.command == "update-evidence":
                    emit(update_evidence(db, a.study, read(a.event), a.expected_version))
                elif a.command == "verify":
                    emit(verify(db))
                else:
                    rows = records(db, a.study)
                    if not rows:
                        raise ResearchError("Unknown study")
                    if a.command == "history":
                        emit([{k: unpack(r)[k] for k in ("version", "hash", "created_at", "event")} for r in rows])
                    else:
                        row = next((r for r in rows if r["version"] == a.study_version), None) if a.study_version else rows[-1]
                        if row is None:
                            raise ResearchError("Unknown study version")
                        value = unpack(row)
                        if a.out:
                            save_reports(a.out, value["bundle"], value["analysis"])
                        emit(value)
        return 0
    except (ResearchError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        # File errors must not expose operator paths in sharable CLI output.
        message = "File operation failed; check the supplied path and permissions" if isinstance(exc, OSError) else str(exc)
        print("Error: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
