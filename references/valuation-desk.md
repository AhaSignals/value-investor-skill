# From an investment idea to a checkable valuation

Start with the question and the available evidence. Do not turn an attractive story or a low multiple into a target price. The local desk joins source capture, financial history, conditional calculations and a research notebook; the assistant still reads filings and challenges assumptions.

## Open the desk

```bash
python3 scripts/investor.py desk
```

Open the printed `http://127.0.0.1:8765` URL. Python 3.9+, no pip dependencies or model API. Windows: `py -3`. The server accepts only loopback access, uses a session token for changes and serves a fixed set of reports. Stop with Ctrl+C. Do not deploy it as a public/multi-user server. `--port` changes the port; `--workspace` chooses where private captures go.

Enter one supported US nonfinancial company. Live capture explicitly accesses public sources; frozen MSFT, KO and CAT financial examples work offline. Public examples contain dated SEC extracts, not redistributed price histories. Source blocking, identity ambiguity, conflicting facts and missing debt must remain visible. A new legal issuer cannot silently inherit a predecessor's financial history.

The notebook lives in the tab until exported. Export before changing companies or closing it. Restore imports inputs only, clears the review checkbox and requires recalculation. Local exports are not independently timestamp-attested. Raw local captures retain provider rights.

## Choose economics, then a method

| Business | First model to consider | Evidence needed before calculating |
| --- | --- | --- |
| Durable positive equity cash generation | Equity DCF + reverse DCF | Reinvestment, financing, current diluted shares, sustainable cash growth and cost of equity |
| Mature or cyclical operating company | Normalized earning power | Full-cycle cash, maintenance spending, working capital and financing; never a peak-year extrapolation |
| Bank | Common-equity residual income | Common book, matching normalized ROE, credit losses, payout and regulatory capital |
| REIT, insurer, distressed or early loss-making company | Specialist asset/equity/event analysis | Sector accounting and capital requirements; do not force a positive-cash model |
| Clinical-stage company or fixed-cash merger | Existing event scenario engine | Conditional outcome payoffs, costs, financing and dated evidence; no invented success probability |

Model selection is an explained research decision, not an automatic sector classifier. Bank calculations accept reviewed inputs; the automatic US operating-company downloader does not normalize bank accounts. Negative cash, speculative turnarounds and buyback forecasts are outside the three new models' supported input ranges.

## Owner earnings: a bridge that needs judgment

Buffett's 1986 discussion distinguishes accounting earnings from the cash left after the investment needed to maintain competitive position and unit volume, including necessary working capital. Read the [original letter](https://www.berkshirehathaway.com/letters/1986.html).

The displayed **CFO minus cash PP&E / annual weighted diluted shares** is only a screening proxy. It is not normalized owner earnings or cash per current diluted share. Investigate maintenance versus growth capex, leases, acquisitions, working-capital timing, recurring stock compensation, financing and share changes. Growth consumes investment. Explain a supported range instead of silently replacing all spending with depreciation. Do not charge the same stock compensation twice through both the starting cash estimate and future dilution.

For a Buffett-style review, explain how the business earns money, evidence of customer retention/pricing power, incremental returns on capital, reinvestment opportunities, balance-sheet resilience, management's allocation choices and the strongest competing explanation. A qualitative moat claim must point to evidence. An apparent price discount depends on those assumptions; it is not a statistical safety guarantee.

## Deterministic models

`python3 scripts/investor.py value examples/valuation/msft.json` returns JSON with assumptions, projections, sensitivity, input hash and warnings. `--out <new-file.json>` saves without overwriting. All four bundled valuation inputs are **illustrative assumptions**, even where the name is a real company. Their comparison price of USD 100 is hypothetical, not a market quote.

- Equity DCF: `g_per_share = (1 + total_cash_growth)/(1 + share_growth) - 1`. Discount each year's equity cash at the required **equity** return. Terminal per-share growth applies the same dilution adjustment. Terminal value is next year's cash / (required return − terminal per-share growth). The implementation conservatively requires total terminal growth below the required return. Cash is after interest, reinvestment and financing requirements: no second debt subtraction, automatic excess-cash addition or WACC substitution.
- Reverse DCF solves only the explicit-period total cash growth matching the supplied price, holding everything else fixed. Bounds are −90% to +100%; outside them the answer is null. It is not an observed market forecast.
- Normalized earning power: reviewed equity cash per share / required equity return, assuming zero growth forever. A terminal zero-growth perpetuity still needs sustainable maintenance spending.
- Residual income: opening common book + discounted `(ROE − required return) × beginning common book` during the explicit horizon. Book grows by retained earnings. Excess income becomes zero after that horizon. Review clean-surplus accounting and regulatory capital. See [Damodaran on financial firms](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf).

Sensitivity changes required return by ±1 and ±2 percentage points, omitting invalid combinations. The chart is a conditional comparison, not a probability distribution. Large terminal contributions are flagged.

## Turn an idea into a research workflow

1. Write the economic mechanism and what the present price would require.
2. Retrieve original filings; record periods, units, publication/observation clocks and missing fields.
3. Choose a method and review the normalization bridge. Use code for arithmetic; use the model for extraction, explanation and competing hypotheses.
4. Save the assumptions and a measurable falsifier. A catalyst means a future observation to review, not a promised price move.
5. Export a dated snapshot. When new evidence arrives, compare against the original; use existing ledger commands for preserved source-dependent revisions. A notebook export does not automatically enter the ledger.
6. Score a forecast against the later disclosed metric before telling a success story. Record misses and exclusions as carefully as matches.

An LLM can organize a finite watchlist and propose investigation priorities. It cannot certify whole-market coverage, verify a filing it did not read, or make its token cost disappear. Ask for an evidence-linked reason, alternative explanation and next check for each shortlisted company; use `scan-batch` only on reviewed normalized inputs.

## PIT and evaluation boundaries

`python3 scripts/investor.py pit-check <batch.json>` delegates to the separately installed `ahasignals_pit.audit_batch`. Follow the [free PIT workflow](https://ahasignals.com/guides/financial-research-workflow/) for its schema and installation. No silent dependency installation. Missing package returns **UNKNOWN**; a library PASS is limited to declared timestamps, context, versions and evidence fields. It does not authenticate source contents, prove candidate completeness, reconstruct the model's knowledge or validate investment returns.

The [frozen company observations](https://ahasignals.com/research/company-pit-observations/) are reusable evidence packets with a defined universe and capture clocks, not an unrestricted historical market database. Today's capture of old accounts does not prove that your pipeline knew them years ago.

```bash
python3 scripts/investor.py review-forecasts examples/forecast-review.json
```

This scores a declared frozen financial forecast against a subsequently available observation, with signed/absolute errors and null percentage error for an actual value of zero. Units are not pooled. Dates must satisfy freeze < period end < outcome availability. The dates are caller declarations, not attestations. This is **forecast review, not a return backtest**. A credible strategy backtest additionally needs an ex-ante universe, delistings, time-valid inputs, execution assumptions, corporate actions, costs and leakage controls. Those are not supplied by this release.
