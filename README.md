# value-investor-skill

## Is this stock worth its price?

Research the business, test the valuation, and see what today's price assumes.

**By [AhaSignals](https://ahasignals.com)** · [中文](README.zh-CN.md) · [Worked demo](docs/demo.md) · [Input guide](references/input-contract.md) · [MIT](LICENSE) · [Roadmap](docs/roadmap.md)

![A fictional $40 stock: same price, different assumptions](assets/demo.svg)

> “This stock is $40. What has to go right to justify that price—and what would change the answer?”

A research skill for your AI assistant, backed by local Python tools. The assistant reads and explains evidence; the code calculates scenarios, checks declared evidence dates, and preserves revisions. **No brokerage connection.**

## Try it in one minute

Python 3.9+; no pip packages, market-data credentials or model calls needed for this **fictional offline demo**.

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/investor.py demo --out output/demo
```

Open `output/demo/before/research.html`, then `output/demo/after/research.html`.

The demo computes the $40 scenarios, freezes the original research, applies a source withdrawal, and shows which estimates become unavailable. It also runs the $100 cash-offer / $92 stock example. Existing demo ledgers are never overwritten; use a new output directory to rerun.

## Install the skill

After cloning, choose your agent's skill directory:

```bash
python3 scripts/install.py --host codex
# Or:
python3 scripts/install.py --host claude
```

The installer copies the self-contained skill and refuses to overwrite an existing installation. Reload your agent's skills, then ask:

> Use value-investor-skill to research this company. Explain what the share price requires, which evidence supports those assumptions, and what could change the conclusion.

For Codex, you can explicitly invoke `$value-investor-skill`. The package includes standard SKILL.md metadata and Codex UI metadata. Installation layout and copied-package execution are tested; the project does not certify every host/model version. Your host supplies the AI and any browsing access; model and data costs depend on that setup. You can also read [SKILL.md](SKILL.md) directly in a tool-enabled assistant.

## Five questions, inspectable answers

| Ask | Get |
| --- | --- |
| **How does this company make money?** | A business brief, funding needs and the event that could change value. |
| **What could it be worth?** | Explicit scenarios with cash, debt, costs and dilution. |
| **What does the price already assume?** | Price-matching assumptions, with underidentification made visible. |
| **What am I missing?** | Counterevidence, missing inputs and reasons to withhold conclusions. |
| **What changed since last time?** | New evidence, affected estimates and preserved prior versions. |

The business analysis and source judgments are performed by your AI assistant/researcher. The CLI does not independently discover a company's intrinsic value or generate a validated probability. Read the [research protocol](references/research-protocol.md).

## The $40 example

*Fictional inputs. Values are assumed present values per share.*

| Favorable value | Unfavorable value | Favorable weight that matches $40 |
| ---: | ---: | ---: |
| $80 | $20 | 33.3% |
| $60 | $20 | 50.0% |

**Which evidence supports $80 rather than $60?** That is the next research question.

These are separate two-state calculations, not event probabilities or a confidence interval. One share price can fit multiple assumptions. When the source supporting launch timing is withdrawn, the demo marks both dependent favorable estimates `NEEDS_REVIEW`, preserves the old version, and withholds a new number. [See the full before/after example](docs/demo.md).

## Try these questions

- “Research this company from primary sources. What must be true for today’s price to make sense?”
- “Here is my investment thesis. Find the strongest evidence against it.”
- “This filing changed. Compare it with my saved research and show which assumptions need review.”

Your assistant needs source access or documents you provide. Missing evidence stays missing.

## What AhaSignals adds

- **Price and evidence stay separate.** Changing the price does not change the supplied state economics. The research instructions prohibit using price to manufacture a desired probability.
- **Time belongs to the evidence.** Publication and observation timestamps are distinct. Future or withdrawn evidence blocks dependent estimates.
- **Financing has two sides.** New capital and new shares enter the same per-share calculation.
- **Updates leave a record.** SQLite snapshots bind inputs, outputs and source events; revisions do not overwrite earlier judgments.
- **Unknown stays unknown.** v0.1 does not estimate calibrated probabilities or an executable valuation gap. It returns `NOT_ESTIMATED` / `NO_QUOTE` alongside useful scenario arithmetic.

These are verifiable design choices, not claims of superior investment performance or claims that all other research tools lack them.

## Use your own research

Start from a bundled JSON example, replace every fictional input with reviewed evidence/assumptions, set `fictional` to `false`, and supply real source URLs. Preserve explicit unknowns. Do not copy example values into a real company analysis.

```bash
python3 scripts/investor.py analyze my-research.json --out output/my-review
python3 scripts/investor.py freeze my-research.json --db output/my-ledger.sqlite
python3 scripts/investor.py verify --db output/my-ledger.sqlite
```

[Full contract, commands and revision workflow →](references/input-contract.md)

An optional [SEC helper](scripts/fetch_sec.py) discovers recent filing references by CIK and acceptance-time cutoff. It requires a caller identifier, makes an explicit network request, and does not retrieve every historical filing or calculate a valuation.

## Scope and limits

**Available:** installable skill; deterministic equity-to-per-share scenarios; conditional two-state inversion; source-date/dependency checks; append-only local snapshots; revision comparison; offline HTML/Markdown/JSON reports; fictional clinical and merger demos; optional SEC filing-index discovery.

**Not claimed:** a calibrated clinical model, automated whole-market research, a complete DCF engine, a statistical value distribution from uncalibrated scenarios, portfolio advice, continuous alerts, brokerage execution, or validated alpha. Clinical and cash-merger research have specific checklists; other companies require a suitable user-supplied model.

Declared source metadata is not authenticated fact. Historical evidence filtering cannot remove an LLM's pretraining knowledge. Local hashes detect inconsistency but do not make a database administrator-proof. Source redistribution rights remain separate from the software license.

## Verify and contribute

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_public_identity.py
python3 scripts/package_release.py --out dist
```

The tests cover arithmetic, dilution, source cutoffs, price freshness, invalidation, concurrent-version conflicts, duplicate events, restart recovery, tampering detection and clean copied installations. They do not measure investment returns. [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

If you try it, an issue with a reproducible redacted case is more useful than a screenshot of a target price. Do not post private holdings, credentials or licensed source documents.

AhaSignals is an independent research publisher. Research and education only; not investment, trading, legal, tax or medical advice. Third-party names identify factual sources or compatibility context, not affiliation or endorsement. MIT-licensed code and original fictional fixtures; third-party source rights are not granted by this license.
