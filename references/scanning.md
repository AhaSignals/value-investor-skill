# Research screens: from an anomaly to a question

Read this when the user asks to scan financial statements, compare historical P/E, examine a value trap, or add chart context to fundamental research. Commands run offline on supplied, normalized observations. They do not download a market universe, parse arbitrary PDFs automatically, or establish intrinsic value.

## Start from the user's company

With browsing, retrieve issuer annual reports and notes plus a permitted price source. Without browsing, ask for the annual reports or exported data. Extract into the [scan input contract](scan-input.md), preserving source URLs, publication and observation times, currency, units, reporting perimeter and adjustments. Show the few material extracted figures and their source locations for review. Do not make an ordinary user hand-author JSON. The host may assemble the bundle; the Python tool checks structure and arithmetic, not whether the extraction is true. Missing fields stay missing; use an empty list for an unavailable module.

For annual financials, reconcile net income, operating cash flow and capex to their respective statements. Explain that CFO minus capex is a simplified cash-flow measure, not owner earnings or cash freely distributable to shareholders. Read stock compensation, lease obligations, working capital, debt maturities, segment and accounting-policy notes. The screen covers nonfinancial operating companies; banks, insurers and property trusts require sector-specific definitions and should not be forced through this contract.

Run `python3 scripts/investor.py scan input.json --out <new-directory>`. For a supplied watchlist, use `scan-batch` with a JSON list of company bundles. Results preserve input order and do not rank investment attractiveness. Reports contain the calculation, admitted source rows, exclusions, input hash, and next research questions. No data provider credentials are needed for the fictional demo; real data access depends on the host and source permissions.

## Three scanning workflows

| Workflow | Measurements | Question it should open |
| --- | --- | --- |
| Financial statements | Annual revenue growth, margin, CFO/net income, CFO minus capex, net debt, diluted-share growth | Are earnings supported by cash, and does growth benefit each share? |
| Valuation history | Trailing P/E, prior-month mean/median, empirical percentile and distance from median | What changed in earnings quality, growth, risk, rates or capital allocation? |
| Price context | Daily OHLC validation; close-based 50/200-observation averages, distance from averages, drawdown over at most 252 observations | Which dated fundamental event could explain the price movement? |

The price workflow does not detect candlestick patterns, predict reversals or provide entry/exit timing. Moving averages summarize price history, not intrinsic value. Drawdowns use split-adjusted closes and exclude dividends; they are not total returns. Market holidays are not inferred, and missing sessions can change these statistics. Gaps over seven calendar days or mixed adjustment bases withhold price-history statistics.

## Mean reversion is a hypothesis

Separate **operating reversion** (margins, working capital or returns on capital), **multiple reversion** (P/E), and **price reversion** (moving averages). A low multiple may reflect temporarily inflated cyclical earnings; a historical high margin may never return after competition or technology changes. Do not import a historical mean as a fair-value target.

Before using a reversion scenario, identify:

1. The economic mechanism: capacity exits, inventory normalization, temporary costs or another sourced explanation.
2. The comparable regime: business mix, accounting, growth, capital intensity, rates and risk. `comparable_regime` is the researcher's declaration, not a statistical test or model certification.
3. The denominator: trailing versus forward earnings, positive earnings, one-offs and split adjustments. Do not mix definitions or retrospectively use restated EPS unavailable at the historical close.
4. Survival and timing: liquidity runway, debt maturity, dilution and the time required for normalization.
5. A falsifier: the observation that would make the change structural rather than temporary.

Historical mean, median and percentile are descriptive. No stationarity test, fitted reversion speed, forecast probability, expected return or backtested edge is supplied. A percentile of zero means only that the current P/E is below every admitted baseline observation. It is not a zero-percent loss probability.

For a margin-of-safety discussion, build explicit downside/base/upside cash-economics scenarios with the existing `analyze` workflow. Explain the sensitivities and missing inputs. Do not calculate a recommended purchase price from the historical P/E median. A price discount to an assumed scenario remains conditional on that scenario.

## Evidence handoff

Each flag must produce an observation, a source/date, a plausible alternative explanation, and a next document or falsifier. Research the flagged item, then pass reviewed assumptions and source dependencies into the existing scenario/ledger workflow. Scan exports are immutable-by-convention files with input hashes, **not** automatically registered ledger revisions. Withdrawing a source and rerunning a scan excludes its rows; older admitted observations remain dated and exclusions stay visible. Revise saved scenario studies using the existing evidence-update commands separately.

## Primary reading

- [SEC: Beginners' Guide to Financial Statements](https://www.sec.gov/about/reports-publications/beginners-guide-financial-statements): roles of statements and management discussion.
- [Aswath Damodaran: P/E fundamentals](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/invfables/peratio.htm): growth, payout and risk determine comparable multiples.
- [Aswath Damodaran: Market Timing Approaches](https://pages.stern.nyu.edu/adamodar/New_Home_Page/invfables/mkttimingapproaches.htm): limits of historical ranges and mean-reversion arguments.

These sources inform the research method; they do not endorse this project or validate its implementation.
