# Research protocol

## Primary evidence

Start with issuer filings, dated investor-relations releases, transaction agreements, trial registries and regulator documents relevant to the specific event. Preserve source URL, document/version identity, publication time, observation time and the passage supporting the claim. Read the source rather than citing a search snippet. A company statement remains a company statement, not independently verified fact.

If a document can be revised at its URL, preserve a permitted snapshot or excerpt and hash, or state that byte-level reproduction is unavailable. Do not redistribute raw third-party documents without appropriate rights. The engine validates structure and declared timestamps; it does not authenticate the source content or evaluate legal rights.

For SEC filing discovery, the optional helper uses the [SEC submissions API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). It filters recent references by acceptance timestamp. Older filing segments, ticker resolution, filing contents and historical coverage completeness require separate research. Avoid treating current companyfacts aggregates or later comparative values as evidence available at an earlier cutoff.

## Clinical-stage company checklist

Define each event separately: trial initiation, endpoint success, regulatory submission, approval and commercialization. Explain endpoint, comparator, population, statistical uncertainty, follow-up and safety limits. A first-dose event is not an approval forecast. Use relevant reference classes only when their definitions and evidence support the comparison; never invent a Bayesian likelihood or a precise success probability.

For economics, make launch timing, patient population, penetration, net price, margins, future development/commercial costs, cash, debt and dilution explicit. Avoid charging the same modeled failure risk once in scenario weights and again in an arbitrary discount rate. Dependent events need a conditional/joint model; do not multiply marginal probabilities as though independent.

v0.1 accepts present-value scenario inputs, not an automatic clinical DCF or validated medical model. If these inputs are unavailable, produce a research brief and missing-input list instead of manufacturing values.

## Fixed-cash merger checklist

Read the agreement and amendments. Identify consideration, closing conditions, funding, approvals, timing, termination rights, dividends and break-value assumptions. Treat alternative deal terms or consideration changes as new scenarios. Distinguish an undiscounted teaching example from a dated, cost-aware valuation.

A single price generally does not identify physical completion probability. Pairwise algebra is conditional on assumed payoffs and discounting. It does not include an independently estimated risk premium, carrying cost, spread execution, or portfolio suitability.

## Other company types

Use `general_scenarios` only for explicit user/researcher-supplied state economics with documented method and limits. Do not force a bank, insurer, commodity producer or early-stage company into one unsupported generic DCF. The name of the skill does not imply universal sector coverage.

## Updates

Compare new documents with the frozen evidence set. A withdrawn source invalidates affected outputs, not necessarily the entire company thesis. Distinguish factual changes, assumption changes, price changes and corrections. A price update alone cannot revise a price-blind probability or core value. Explain unreviewed inputs and preserve the prior version.

## Claim limits

Do not report profitability, calibration, avoided losses or better user decisions without an appropriate experiment. Tested arithmetic and correct timestamp rejection do not establish investment performance. Record failed and withheld conclusions as well as supported ones.
