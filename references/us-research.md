# Research a US stock from its name

```bash
python3 scripts/investor.py research MSFT --out output/msft
# Microsoft, Apple and quoted English company names also work.
python3 scripts/investor.py replay output/msft --out output/msft-replay
```

Open `research.html`. Give `research.md` to your assistant for business interpretation, source review and counterevidence. No API key or pip dependency is required; Python 3.9+, network access and writable files are required. Run from the installed skill directory, or use an absolute script path. Without `--out`, a fresh dated directory is created. Existing research is never overwritten.

## What happens automatically

1. Resolve the security using the SEC ticker directory. Ambiguous share classes require a ticker.
2. Retrieve SEC submissions, US-GAAP Company Facts and the latest annual 10-K document. Extract up to five annual periods, retaining units, accession numbers and per-field publication dates.
3. Request public Yahoo Finance daily OHLC and split events. Retain up to 1,260 bars and 61 completed-month P/E observations. Availability varies by company/provider; these are limits, not a promised coverage count.
4. Calculate cash conversion, CFO minus cash capex, net debt when complete, share changes, descriptive P/E statistics, moving averages and drawdowns. Save a dated HTML/Markdown/JSON brief, screen and selected local filing passages.
5. The AI host reads the brief and relevant filing sections, explains the business and investment requirements, investigates competing explanations, and identifies what would change the conclusion. The deterministic CLI supplies calculations and research questions; it does not generate an intrinsic-value judgment by itself.

## Definitions that matter

- Supported automatic scope: USD, US-GAAP 10-K nonfinancial operating companies. Banks, insurers, REITs, ETFs, foreign 20-F issuers and unsupported taxonomies need another workflow. Company name resolution is not universal multilingual entity recognition.
- Standard XBRL tags only. Custom tags or conflicting contexts stay unknown. Missing capex/debt is never zero. Debt requires a complete total or non-overlapping complete components; commercial paper alone cannot prove all other short-term borrowing is zero. Cash excludes investments. This can leave a useful report marked `PARTIAL`.
- Annual figures use the latest values available at capture, including subsequently restated comparative years. Share-growth comparisons are withheld when split comparability is unresolved. CFO minus cash capex excludes financing leases and some economic costs; it is not owner earnings.
- Historical diluted TTM EPS uses annual EPS + current YTD EPS − prior YTD EPS where available. This is an approximation: changing weighted shares mean it can differ from a vendor's exact trailing measure. Each fact must have been available before the sampled session opened. Missing acceptance times use the next UTC day after filing. Later restatements are excluded for earlier sessions.
- Provider OHLC/close is used, not dividend-adjusted close. EPS is aligned using subsequent split events after its publication. Complex corporate actions require manual review. Current UTC-date bars are withheld even if a local session may have closed.
- Monthly samples use each completed month's final **supplied** session. The tool does not verify exchange calendars or prove that every session is present. Historical averages describe the admitted sample. `DESCRIPTIVE_NONCOMPARABLE` means the business regime has not been reviewed: it is not a fair-value baseline or mean-reversion forecast.
- Latest captured EPS with the latest completed close is shown separately from the completed-month screen. Timestamps and publication/price dates may differ. This is a current-source reconstruction, not a point-in-time backtest or proof that model training contains no later information.

## Sources, access and failures

[SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) · [SEC developer access guidance](https://www.sec.gov/about/developer-resources) · [Yahoo adjusted-close definition](https://help.yahoo.com/kb/SLN28256.html).

Requests are sequential, at least 1.05 seconds apart, with bounded response sizes and timeouts. SEC requests identify AhaSignals; you may set `SEC_USER_AGENT` to your own organization/contact. Request headers are never saved. A 403/429 stops that provider attempt: no proxies, login bypass, crumb extraction or aggressive retry. Price/document failure produces an explicitly partial report when SEC financials remain usable. SEC identity/financial failure stops the run; use a new output directory after resolving it.

Yahoo's public endpoint has no guaranteed availability or service contract. Data access and redistribution rights are separate from the MIT software license. Review applicable provider terms for your use. Do not publish the raw capture or assume the project grants data redistribution rights.

## Reproduce, do not backdate

`capture.json` records actual observation times and source hashes; `sources/` retains private original responses. `replay` verifies them and performs no network calls. Keep the original folder: the replay report does not duplicate its raw cache. Replay output can change with a new calculation version; pin the software tag for exact reproduction. Hashes detect changed bytes, not independently authenticated facts.

The public [Microsoft example](../docs/msft-research.md) includes a frozen **SEC financial extract** and expected checksums. It reproduces the financial screen offline. Its separate live-run receipt documents the larger private capture; it does not redistribute Yahoo price history or the annual filing.
