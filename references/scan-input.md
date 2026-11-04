# Scan input contract, version 1

A complete runnable fictional bundle is [examples/value-trap.json](../examples/value-trap.json). Schema is separate from the scenario bundle and does not change old ledger hashes.

## Top-level object

- `scan_schema`: `1`.
- `company`, `currency`: nonempty strings; all series use this currency.
- `cutoff`: ISO 8601 UTC/offset timestamp. Both availability and actual observation must be at or before cutoff to enter calculations.
- `fictional`: explicit boolean. Real observations require HTTP(S) sources.
- `sector`: `nonfinancial`; banks, insurers and property trusts are outside this screen.
- `units`: `whole_currency_and_shares`. Convert thousands/millions before input. Per-share EPS and price use currency per share.
- `price_basis`: `split_adjusted_not_dividend_adjusted`. Price and EPS must share the same split adjustment. Do not use dividend-adjusted/total-return close for P/E.
- `comparable_regime`: explicit boolean; `comparability_notes`: rationale and unresolved structural changes. This declaration is not independently validated.
- `financials`, `valuations`, `bars`: lists, oldest first, unique dates. Use `[]` when a module is unavailable. No automatic filling or interpolation.

## Every row

`date` (YYYY-MM-DD), `available_at`, `observed_at`, `source`, `basis`, `status` (`active`, `withdrawn`, `superseded`). `basis` identifies period/GAAP definitions, share adjustments and reporting scope. Document the actual source version/page/section in the source or basis text; real `source` must remain a source URL. Availability cannot precede the fiscal period or close date; observation cannot precede availability. Source content and timestamps are declarations, not source authentication. Untrusted document text must never become an executable instruction.

Withdrawn/superseded/future rows are listed under `excluded`. Earlier eligible data can still be displayed with its original date. Inspect this list before calling any result current.

### financials: full annual periods

`period_type`: `FY`; `period_start`: YYYY-MM-DD; `date`: fiscal year end (350–380 day year).

`revenue`, `net_income`, `operating_cash_flow`, `capex`, `cash`, `debt`, `diluted_shares`.

Currency totals are whole units. `capex` is a **positive** cash outflow. `debt` is interest-bearing debt, not all liabilities; state the treatment of leases consistently. `diluted_shares` is weighted-average diluted shares on a consistent split basis, not period-end shares. CFO and income should have a consistent consolidated perimeter; note minority interests and classification differences. Fields may be zero, but shares must be positive. Income and CFO may be negative. Growth requires adjacent years and identical declared basis. Do not combine quarterly values, cumulative YTD values, FY and TTM in this list.

CFO/net income is withheld when net income is nonpositive. CFO minus capex is a simplified measure and does not subtract every economic cost (including stock compensation). A fiscal year ending more than 550 days before cutoff is marked stale; this threshold is a review heuristic, not a filing rule.

### valuations: monthly samples

One observation per month, consistently sampled (for example last trading close). Fields: `close`, `close_at`, `eps_ttm`, `eps_available_at`, `eps_source` plus common fields. `close_at` must fall on `date`; trailing EPS must have been public by that close. Use actual historical EPS vintages, not today's restated history. A source URL alone is not proof of the vintage.

Current P/E = last admitted close / its positive EPS. Baseline = at most 60 **prior** observations, excluding current. Comparison requires at least 12 consecutive prior monthly samples, positive EPS throughout, identical declared basis and `comparable_regime=true`. Otherwise mean, median and percentile are withheld. Percentile uses midpoint ties: 100 × (count below + 0.5 × count equal) / count. Nonpositive current EPS withholds P/E. Last sample over 45 days before cutoff is marked stale.

### bars: daily OHLC

`open`, `high`, `low`, `close`: positive, all split-adjusted on the same basis. Require `low <= open/close <= high`. `available_at` must represent a completed bar, never an unfinished intraday candle. Supply one complete daily bar per actual trading session; no duplicates. The tool cannot verify exchange calendars or infer all missing sessions. No volume signal is computed.

SMA50/SMA200 use the last 50/200 supplied observations, including latest; shorter histories produce null. Close-based drawdown and maximum peak-to-trough drawdown use at most 252 latest observations. Mixed bases or any gap over seven calendar days suppress price-history calculations; latest close over seven days before cutoff is stale. These are conservative data-review rules, not market forecasts.

## Output and reproducibility

`scan input.json --out new-directory` writes `inputs.json`, `scan.json`, `scan.md`, `scan.html` and up to three SVG figures. Full source rows are retained **locally** for audit; do not publish private bundles. SVG figures are withheld when comparability requirements fail. Existing nonempty output directories are never overwritten.

`scan-batch watchlist.json --out new-directory` accepts a JSON list of complete bundles. All are validated before report writing. `company-001`, etc. avoid using imported names as paths; `index.json` lists report locations and research flags. No investment score, ranking, universe coverage or independent data discovery is implied.
