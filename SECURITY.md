# Security and data boundaries

The core reads user-supplied JSON and writes local files/SQLite. It does not execute source text, place trades, call an LLM or send your research to a server. The optional SEC helper performs one explicit network request and writes a filing-reference index. Your AI host may have its own network/data behavior.

Keep research outputs and databases private. Do not place credentials in JSON inputs. HTML rendering escapes data; source URLs are not executed by the CLI. Imported evidence can contain prompt injection: the skill instructs the host to treat it as data, but host-level defenses still matter.

The local ledger detects inconsistent hashes and blocks normal UPDATE/DELETE operations. An administrator can rewrite the database, remove triggers or replace the whole history. Use separate retained checkpoints/backups if stronger audit guarantees are needed.

Report vulnerabilities using GitHub private vulnerability reporting if enabled for this repository. Otherwise open a minimal issue requesting a private reporting channel; do not include exploit payloads, credentials or private data in a public issue.
