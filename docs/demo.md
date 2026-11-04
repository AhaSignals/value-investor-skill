# Run the demo

## Low P/E, weak cash generation

```bash
python3 scripts/investor.py scan-demo --out output/value-trap
```

Open `output/value-trap/scan.html`. The third fictional case is a nonfinancial manufacturer: P/E 10 versus a prior-month median of 20, net income 15 million, operating cash flow 5 million and capex 8 million. Cash after capex is negative 3 million; net debt is 35 million. The screen flags cash conversion, rising net debt and diluted shares before asking whether the multiple discount is justified.

The report includes cash-versus-profit, P/E-history and price-context SVG charts. Change `comparable_regime` to false and run `scan` into a fresh directory: the historical P/E baseline and chart are withheld. Change current EPS to zero: current P/E is withheld too. Withdraw a financial source: its row is excluded, earlier data stays dated, and the exclusion is reported. These checks are not estimates of investment returns.

[Inspect the fictional inputs](../examples/value-trap.json) · [Method](../references/scanning.md) · [Input contract](../references/scan-input.md)

## Scenario and evidence-withdrawal cases

This is a real execution of fictional inputs, not a real-company forecast.

```bash
python3 scripts/investor.py demo --out output/demo
```

1. Open `before/research.html` under the output directory. Inspect the business, material event, values, price assumptions and missing evidence.
2. Open `after/research.html`. The launch-timing assumption was withdrawn; dependent favorable values are now withheld. The unrelated downside remains available.
3. Read `changes.json` and run the history commands below to see the preserved original inputs.
4. Open `merger/research.html` for the fixed-cash teaching example.

```bash
python3 scripts/investor.py history fictional-clinical --db output/demo/research.sqlite
python3 scripts/investor.py show fictional-clinical --study-version 1 --db output/demo/research.sqlite
python3 scripts/investor.py verify --db output/demo/research.sqlite
```

## The $40 question

The inputs assume favorable values of $80 or $60 and an unfavorable value of $20. The matching higher-state weight is `(price − low) / (high − low)`: 33.3% or 50.0%. These are separate slices, not measured probabilities or a confidence interval. The $60/$80 pair does not contain the $40 price and is marked outside the pair.

The next research question is which evidence supports the favorable economics. No clinical success estimate is supplied. The examples do not collapse trial success, approval, launch and commercial adoption into one clinical probability.

## Evidence withdrawal

`examples/withdrawal.json` describes a scripted fictional source withdrawal. The event checks both the expected study version and old evidence hash. Applying it twice yields the same receipt; changing its content while reusing its ID fails. An active replacement source requires an explicitly reviewed full revision.

`NEEDS_REVIEW` does not mean the stock should be sold. It means specified estimates no longer have usable supporting inputs at the new research cutoff.

## The $8 cash-offer gap

A hypothetical $100 offer and $92 share price match an 80% completion-state weight if break value is $60, or 60% if break value is $80. This teaching example sets discounting to one and omits dividends, fees, financing, execution constraints and risk premia. Neither weight is an independently estimated deal probability, and the $8 spread is not known profit.

## A 60-second walkthrough

- 0–10 seconds: ask what must happen to justify $40; keep the fictional-data label visible.
- 10–25 seconds: show the two favorable assumptions and their different price-matching weights.
- 25–40 seconds: expand source dates and the unknown probability; show the supporting assumptions.
- 40–55 seconds: open the after-report; the withdrawn source blocks dependent values.
- 55–60 seconds: show that version 1 is still present and the ledger verifies.

The checked-in SVG is a summary of example values, not a screenshot of a live market system. Generated HTML is the actual inspectable report. No real-company results or financial performance are claimed.

[查看由代码生成的完整研究输出](demo-output.md)。
