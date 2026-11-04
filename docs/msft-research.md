# Microsoft: profits grew, cash after investment fell

**Real company; frozen observation at 2026-11-04 12:41 UTC. USD billions unless stated.** A dated research example, not a live quote or an investment recommendation.

Microsoft earns revenue from enterprise productivity, cloud services and personal computing. Its AI/cloud expansion requires infrastructure before all associated revenue is known. The research question is whether future usage and cash generation can justify that investment—not whether a low historical P/E alone implies a rebound.

## The financial bridge

| Fiscal year ended June 30 | FY2025 | FY2026 |
| --- | ---: | ---: |
| Revenue | 281.724 | 331.839 |
| Net income | 101.832 | 133.749 |
| Operating cash flow | 136.162 | 182.935 |
| Cash purchases of property/equipment | 64.551 | 115.948 |
| CFO minus cash capex | **71.611** | **66.987** |

Operating cash flow increased by **46.773 billion**, while cash capex increased by **51.397 billion**. Cash after those purchases therefore fell **4.624 billion** despite rising reported profit. Source: [Microsoft SEC Company Facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json); per-field accession, units and publication times are preserved in the [frozen extract](../examples/msft-financials-2026-11-04.json). The [FY2026 annual filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) supplies the business and investment context.

This bridge is a useful starting point, not a conclusion that the investment is wasteful. Cash capex is lumpy; it does not include all lease additions, and CFO is affected by working capital and stock compensation. The automatic mapping could not establish a complete comparable debt definition, so **net debt stays unknown**. Do not read that as zero debt.

## The competing explanations

**Productive expansion:** capacity supports demand that later converts into durable cash flow. Test this against subsequent segment revenue, margins, utilization disclosures and cash generation after the expanded asset base is operating.

**Investment outruns economics:** commitments, replacement cycles, depreciation and operating costs grow faster than monetization. Inspect the annual filing's cloud/AI investment risks, property/equipment and lease notes, purchase commitments, and later quarterly disclosures. The script's selected passages are navigation aids, not a substitute for reading those notes.

What would change the interpretation? Sustained cash generation after investment, with manageable commitments and stable economics, would weaken the overinvestment concern. Persistent capex/commitment growth without corresponding cash generation would strengthen it. Neither outcome is assigned a probability by this tool.

## Price context from the private live run

The capture contained **5 annual periods, 1,260 daily bars and 61 monthly P/E observations**. Latest completed close: **USD 520.99 on 2026-11-03**. Approximate diluted TTM EPS through 2026-09-30: **19.15** (17.95 annual + 4.92 current YTD − 3.72 prior YTD); latest-close P/E: **27.21×**. The completed-month screen is separately dated 2026-10-30: P/E **27.25×**, versus a prior-60-observation median **33.37×**. Sources: SEC facts above and [Yahoo historical prices](https://finance.yahoo.com/quote/MSFT/history/), observed at the capture date.

Economic comparability is **unreviewed**. A lower multiple may reflect a changed investment burden or growth outlook. These descriptive figures do not establish fair value, a bargain or a reversion forecast. Raw price history and filing text are not redistributed here.

## Reproduce the public financial result offline

Use release **v0.5.0** and Python 3.9+:

```bash
python3 scripts/investor.py scan examples/msft-financials-2026-11-04.json --out output/msft-public
```

Open `output/msft-public/scan.html`. [Expected input/result hashes](../examples/msft-financials-expected.json) and the automated fixture test verify the frozen financial calculation. Price and P/E sections are unavailable in this public financial-only fixture by design.

To fetch a new research snapshot and reproduce **your own complete capture**, including prices:

```bash
python3 scripts/investor.py research Microsoft --out output/msft-live
python3 scripts/investor.py replay output/msft-live --out output/msft-replay
```

New live results will differ as sources change. Replay needs the original local source folder and the same software version. Ask your assistant to read `research.md`, follow its filing links, explain the competing hypotheses above, and state the next evidence needed. [Method and coverage](../references/us-research.md).
