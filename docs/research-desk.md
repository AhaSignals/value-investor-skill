# Three companies. Three different research questions.

Observed 2026-11-04 UTC / 2026-11-05 Asia/Shanghai (MSFT captured earlier on November 4). These are reproducible SEC financial extracts, not investment recommendations. Comparative figures use the versions available at capture; they are not historical point-in-time investment signals.

Start the free local desk:

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/investor.py desk
```

Open the printed local URL. Select **Inspect MSFT**, **Inspect KO** or **Inspect CAT** for offline data; type a name to capture supported public sources. No project account, model API or pip dependencies. An AI assistant is optional and uses its own tools and fees. Windows: replace `python3` with `py -3`.

## Microsoft: growth must pay for reinvestment

In the frozen extract, FY2026 net income is USD 133.749 billion; CFO is 182.935 billion and cash PP&E is 115.948 billion. Cash after capex is **66.987 billion**, down from 71.611 billion in FY2025 despite higher profit. It is not automatically owner earnings: leases, replacement cycles, commitments, working capital and compensation need investigation. [Full cash bridge and original filing](msft-research.md).

A defensible next step is to test cash generation after infrastructure investment and ask what utilization, margins and replacement economics must hold. The strongest alternative is that spending is productive capacity whose payoff is delayed; a single year's cash decline cannot establish destruction of value. Conversely, revenue growth alone cannot prove an adequate return on new capital. Check subsequent segment disclosures, cash after investment and commitments.

The separate `examples/valuation/msft.json` is a **method demonstration**: assumed normalized equity cash of USD 9/share, 8% total cash growth, 1% annual share growth, 2.5% terminal cash growth and 10% required equity return over five explicit years. Conditional value is about **USD 134.48/share**. Its hypothetical USD 100 comparison price requires about **0.83%** explicit total cash growth with every other input fixed. Neither number is a Microsoft fair-value finding or current-market claim; the starting cash is a rounded assumption, not a validated owner-earnings bridge.

## Coca-Cola: accounting profit is not the cash available to owners

FY2025 net income is USD **13.107 billion**, CFO **7.408 billion**, cash PP&E **2.112 billion**: cash after capex is **5.296 billion**. The cash figure is much lower than profit. Investigate the cash-flow reconciliation, unusual payments, taxes and working capital before normalizing. The screen cannot identify the cause by subtraction. Customer demand, pricing, volume and distribution economics need separate evidence; a familiar brand alone is not proof of a durable return.

Source: [SEC filing index](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/0001628280-26-010047-index.html). [Frozen rows and per-field provenance](../examples/ko-financials-2026-11-05.json).

`examples/valuation/ko.json` deliberately uses an unverified **illustrative** normalized cash assumption of USD 2.20/share and a 10% required equity return: zero-growth earning power is **USD 22/share**. This does not establish the company's value. Its purpose is to show exactly where a claim about normalization changes the result. A subsequent filing that explains and reverses a temporary cash outflow would change the bridge; continuing cash weakness would challenge it.

## Caterpillar: normalize the cycle and separate financing

FY2024 cash after capex is USD **10.047 billion**; FY2025 is **8.918 billion**. Net income declines from 10.788 to 8.882 billion. Annual diluted weighted shares decline from 489.4 to 472.3 million. The per-share cash proxy therefore falls less than total cash. Repurchases change the denominator but do not establish attractive repurchase economics.

Source: [SEC filing index](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/0000018230-26-000008-index.html). [Frozen rows and per-field provenance](../examples/cat-financials-2026-11-05.json).

Do not capitalize a peak year forever. Review equipment demand, dealer inventories, working-capital swings, maintenance investment and the financing subsidiary before choosing normalized equity cash. The five extracted years need not cover a full cycle. A mean-reversion thesis needs a mechanism—such as a demonstrably temporary inventory cycle—and an explicit way to be wrong. Returning to an old P/E is not that mechanism.

`examples/valuation/cat.json` assumes, for illustration only, USD 15 normalized cash/share at a 10% return: zero-growth earning power is **USD 150/share**. It is not a computed normalized estimate. Separate industrial and finance accounts before using a company-specific valuation.

This live trial also exposed a real extraction defect: a stale `NetIncomeLoss` series obscured newer `ProfitLoss` annual values. The extractor now considers both and withholds conflicting period starts. Regression tests protect that behavior.

## A bank is a different model

`examples/valuation/bank-fictional.json` is fully fictional: common book USD 20/share, ROE 12%, payout 50%, required equity return 10%, five years of excess returns followed by zero excess returns. Conditional value is about **USD 21.69/share**. The downloader does not automatically normalize banks; users must review common-equity scope, credit losses, clean-surplus accounting and capital constraints.

## Reproduce and challenge

```bash
python3 scripts/investor.py scan examples/ko-financials-2026-11-05.json --out output/ko-public
python3 scripts/investor.py scan examples/cat-financials-2026-11-05.json --out output/cat-public
python3 scripts/investor.py value examples/valuation/msft.json
python3 scripts/investor.py value examples/valuation/ko.json
python3 scripts/investor.py value examples/valuation/cat.json
python3 scripts/investor.py value examples/valuation/bank-fictional.json
python3 scripts/investor.py review-forecasts examples/forecast-review.json
```

Use a new output directory when rerunning. The screen preserves unknown debt rather than inferring zero; all public fixtures omit raw prices and filing documents. Change an assumption and inspect sensitivity, then write down the evidence needed to justify that change. [Model formulas, notebook workflow and PIT limits](../references/valuation-desk.md).
