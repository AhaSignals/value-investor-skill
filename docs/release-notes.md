# Value Investor Skill v0.4.0

**8 research workflows in 1 AI skill.** Scan financial statements, compare historical P/E and inspect daily price context alongside business research, valuation scenarios, price assumptions, counterevidence and evidence updates.

## Try the low-P/E case

```bash
python3 scripts/investor.py scan-demo --out output/value-trap
```

Open `output/value-trap/scan.html`. A fictional manufacturer has P/E 10 versus a historical median of 20, but profit of 15 million produces only 5 million operating cash flow and needs 8 million capex. The report asks whether cash conversion, net debt and dilution explain the discount. Three charts accompany dated calculations and research questions.

## What is included

- `scan` for one supplied company bundle; `scan-batch` for a supplied watchlist, without investment scores or rankings.
- Annual cash-flow, margin, debt and dilution checks; monthly trailing-P/E history; daily OHLC validation, 50/200-observation averages and drawdowns.
- Explicit source cutoffs, historical EPS availability, loss denominators, noncomparable regimes, missing/stale data and evidence withdrawals.
- Three fictional cases and four unique demo illustrations in the repository. Seven language guides now cover the new screens, examples and boundaries.
- English/Chinese portable instructions for Claude, ChatGPT, DeepSeek, Grok, Gemini and Kimi. Files and Python are required to run the local engine; chat alone does not install it.

[Method and mean-reversion limits](https://github.com/AhaSignals/value-investor-skill/blob/v0.4.0/references/scanning.md) · [Input format](https://github.com/AhaSignals/value-investor-skill/blob/v0.4.0/references/scan-input.md) · [Zero-install starting point](https://ahasignals.com/value-investor-skill/)

## Downloads

- `value-investor-skill-upload-v0.4.0.zip`: self-contained skill instructions, references, examples and runtime tools.
- `value-investor-skill-v0.4.0.zip`: source, installer, tests, seven guides and illustrations.
- `SHA256SUMS`: checksums for both archives.

Python 3.9+, standard library only. Scanner output version is 1.0.0; existing scenario output remains 0.1.0, preserving prior ledger reproduction. Real data acquisition and normalization are host-assisted. No whole-market downloader, arbitrary PDF parser, reversion probability, return forecast or trading execution is supplied. Historical P/E and moving averages are research context, not intrinsic value or investment advice.
