#!/usr/bin/env python3
"""Fetch a dated SEC recent-filings index. It is evidence discovery, not valuation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.research import ResearchError, timestamp


def select_filings(data, cutoff, cik):
    recent = data.get("filings", {}).get("recent", {})
    rows = []
    for i, accession in enumerate(recent.get("accessionNumber", [])):
        def field(key):
            seq = recent.get(key, [])
            return seq[i] if i < len(seq) else None
        accepted = field("acceptanceDateTime")
        if not accepted or timestamp(accepted) > cutoff:
            continue
        document = field("primaryDocument")
        if not isinstance(accession, str) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
            raise ResearchError("Unexpected accession format")
        if (not isinstance(document, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", document)
                or any(part in {".", ".."} for part in document.split("/"))):
            raise ResearchError("Unexpected primary document name")
        rows.append({"accession": accession, "form": field("form"), "accepted_at": accepted,
                     "url": "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (int(cik), accession.replace("-", ""), document)})
    return rows


def main():
    p = argparse.ArgumentParser(description="Optional live SEC index fetch. Requires SEC_USER_AGENT identifying your organization/contact.")
    p.add_argument("--cik", required=True)
    p.add_argument("--cutoff", required=True, help="ISO timestamp with time zone; filters by SEC acceptance time")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    try:
        if not re.fullmatch(r"\d{1,10}", a.cik):
            raise ResearchError("CIK must contain 1–10 digits")
        ua = os.environ.get("SEC_USER_AGENT", "")
        if not ua.strip() or "\n" in ua or "\r" in ua:
            raise ResearchError("Set SEC_USER_AGENT with a valid organization/contact identifier; it is not saved in outputs")
        cutoff = timestamp(a.cutoff)
        url = "https://data.sec.gov/submissions/CIK%s.json" % a.cik.zfill(10)
        with urlopen(Request(url, headers={"User-Agent": ua, "Accept": "application/json"}), timeout=30) as response:
            raw = response.read(20_000_001)
        if len(raw) > 20_000_000:
            raise ResearchError("SEC response exceeded the size limit")
        data = json.loads(raw)
        result = {"source": url, "observed_at": datetime.now(timezone.utc).isoformat(), "cutoff": a.cutoff,
                  "response_sha256": hashlib.sha256(raw).hexdigest(), "filings": select_filings(data, cutoff, a.cik),
                  "coverage": "Recent-filings segment only. Older segments are not fetched. Empty output does not prove no filings exist.",
                  "boundary": "Filing references only; read and review each document. Current index metadata is not historical proof of the entire source universe."}
        Path(a.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Saved %d filing references. No valuation or probability was inferred." % len(result["filings"]))
        return 0
    except (ResearchError, URLError, OSError, ValueError) as exc:
        print("Error: " + (str(exc) if isinstance(exc, ResearchError) else "SEC fetch or output failed; no successful result claimed"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
