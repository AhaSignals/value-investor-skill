# Input contract and CLI

The executable validator in `core/research.py` is authoritative. See the complete [clinical example](../examples/clinical.json) and [merger example](../examples/merger.json). JSON must be UTF-8. Version 1 is deliberately a small hand-reviewed bundle, not an automatic valuation model.

## Required study fields

- `schema_version`: 1; `id`: stable study identity.
- `company`, `currency`, `business`, `event`, `resolution_rule`, `horizon`, `model_limits`: nonempty text.
- `fictional`: boolean, explicit even for real-company work.
- `archetype`: `clinical`, `cash_merger` or `general_scenarios`.
- `cutoff`: ISO 8601 timestamp with time zone.
- `mode`: `historical_public` uses declared publication time; `as_observed` also requires observed time at or before the cutoff. Historical-public mode does not prove the system actually obtained the evidence then.
- `price`: positive `value`, dated `as_of`, nonnegative `max_age_hours`. Freshness is measured at the study cutoff, not automatically against the current wall clock. A new live review needs a new cutoff and price snapshot.
- `counterevidence`, `unknowns`, `invalidation_conditions`: nonempty text lists. State a real gap or counterargument, not an invented confidence score.

## Evidence

Each item requires a unique `id`, `title`, `claim`, `rights`, `version`, `published_at`, `observed_at`, `kind` and `status`.

Kinds: `reported_fact`, `management_statement`, `assumption`, `counterevidence`.
Statuses: `active`, `withdrawn`, `superseded`.

Real studies require an HTTP(S) `url`. Optional `content_sha256` records a lowercase 64-character content digest; the engine checks its format but does not download or verify bytes against it. Rights text records the supplied position, not a legal clearance. A future, withdrawn or superseded item blocks scenarios referencing it. Unused inadmissible items are shown but do not block unrelated scenarios.

## Scenario economics

Each scenario requires a unique `id`, `label`, `assumptions`, nonempty `evidence_ids` and these numeric fields, all in whole currency units or whole shares (not millions):

```text
net equity = operating_value_pv + cash − debt − other_claims
             + new_capital_net − future_costs_pv
value per share = max(0, net equity / (shares + new_shares))
```

`operating_value_pv` is a supplied, already-discounted operating value and may be negative. Other fields are nonnegative; `shares` is strictly positive. State where each cost is modeled to avoid double counting. New financing affects cash and share count together. A zero floor is a limited-liability modeling convention, not guaranteed recovery; the report flags its application.

Optional `scenario_weights` must cover all scenario IDs, lie in [0,1], and sum to one. Provide `weight_basis`. These are user assumptions; the result remains a weighted scenario value, never a calibrated probability forecast. Only use weights over mutually exclusive, exhaustive states; alternative sensitivities for the same favorable outcome should not be added as if separate outcomes.

## Price inversion

For each distinct low/high state pair:

```text
high-state matching weight = (price − low value) / (high value − low value)
```

Only weights in [0,1] are displayed; other pairs are marked `OUTSIDE_PAIR`. Equal-valued pairs are not inverted. More than two states remain underidentified; the rows are separate two-state slices. No risk-premium estimation, executable-price cost model or decision margin is implemented. `NO_QUOTE` and `NOT_ESTIMATED` intentionally remain the decision/probability outputs.

## Research ledger

Run from the skill/repository directory. Paths to user inputs and outputs can be elsewhere.

```bash
python3 scripts/investor.py analyze examples/clinical.json --out output/review
python3 scripts/investor.py freeze examples/clinical.json --db output/research.sqlite
python3 scripts/investor.py update-evidence fictional-clinical examples/withdrawal.json --db output/research.sqlite --expected-version 1
python3 scripts/investor.py history fictional-clinical --db output/research.sqlite
python3 scripts/investor.py show fictional-clinical --db output/research.sqlite --study-version 1 --out output/prior
python3 scripts/investor.py show fictional-clinical --db output/research.sqlite --out output/current
python3 scripts/investor.py compare output/prior/inputs.json output/current/inputs.json
python3 scripts/investor.py verify --db output/research.sqlite
```

For a fully reviewed replacement bundle:

```bash
python3 scripts/investor.py revise reviewed-next.json --db output/research.sqlite --expected-version 2 --reason "Reviewed new evidence and changed state economics"
```

`freeze` is idempotent for an unchanged latest bundle, but refuses to overwrite an existing study with different input. Revisions require the current version and a nonempty reason; cutoffs cannot move backward. To study a different earlier cutoff, create a separate study ID.

Evidence events contain `id`, `evidence_id`, `expected_evidence_hash`, `cutoff`, `replacement`, `reason`. The hash is SHA-256 of canonical JSON (sorted keys, UTF-8, no extra whitespace). Example generation is visible in the bundled fixture. A replayed event with the same ID and identical content returns the original receipt without adding a row. Reusing that ID with different data fails. Active source replacements require `revise`, because model assumptions must be reviewed first.

Database writes are transactional and use compare-and-swap versions. UPDATE/DELETE triggers prevent ordinary row replacement. Hashes bind inputs, outputs, event, version, prior hash and recording time. `verify` recalculates both hashes and analysis. Local administrators can remove triggers or rewrite a full chain; external checkpoints are needed for stronger assurance. Keep backups outside the application.

Reports are materialized views: `--out` overwrites the report files in that directory, not frozen database history. User records belong in ignored local folders and are not included in releases.

## Optional SEC discovery

```bash
# Set SEC_USER_AGENT in your shell to your organization/contact identifier first.
python3 scripts/fetch_sec.py --cik 1703057 --cutoff 2026-11-02T16:00:00Z --out output/sec-index.json
```

No API key is required by the SEC endpoint. Network access and a proper caller identifier are required. The helper does not store the identifier. Read the returned filings yourself/with your host's browsing tools and curate evidence; it does not create a valuation bundle. A network failure is an error, not evidence that no filing exists.
