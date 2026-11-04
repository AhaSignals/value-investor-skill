# Value Investor Skill v0.5.0

**Enter Microsoft or MSFT. Retrieve public filings and historical prices, scan the evidence, then ask your assistant what the numbers mean.**

```bash
python3 scripts/investor.py research Microsoft --out output/msft
python3 scripts/investor.py replay output/msft --out output/msft-replay
```

Open `output/msft/research.html`. Python 3.9+, no pip packages or API key. The installed skill runs this workflow in hosts with network, Python and writable files; ordinary chat depends on its own browsing tools.

- SEC company resolution, annual statements and the latest 10-K; public daily OHLC and completed-month P/E context.
- Cash conversion, CFO minus cash capex, debt/dilution gaps, dated EPS, split alignment and counterquestions. The AI assistant supplies deep business interpretation.
- Private source capture with checksums and offline replay. Provider blocks stop without bypass; useful financial reports survive price/document failures.
- A [real Microsoft case](https://github.com/AhaSignals/value-investor-skill/blob/v0.5.0/docs/msft-research.md): FY2026 profit grew, but CFO minus cash capex fell from USD 71.611bn to 66.987bn. The frozen SEC financial extract reproduces offline; raw price history and filing text are not redistributed.
- Seven language guides, six assistant entry points, one installable skill and eight research workflows.

Supported automatic scope: US-GAAP USD nonfinancial 10-K companies. Missing fields stay unknown; banks, insurers, REITs and foreign 20-F issuers require other methods. Historical P/E is descriptive, not fair value or a rebound forecast. No trading execution or return claim.

Downloads: `value-investor-skill-upload-v0.5.0.zip` for skill upload; `value-investor-skill-v0.5.0.zip` for full source and tests; `SHA256SUMS` verifies both. Scanner output 1.1.0; scenario output remains 0.1.0.

[Source definitions and replay](https://github.com/AhaSignals/value-investor-skill/blob/v0.5.0/references/us-research.md) · [Start in your assistant](https://ahasignals.com/value-investor-skill/)
