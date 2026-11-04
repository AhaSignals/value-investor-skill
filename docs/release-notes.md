# Value Investor Skill v0.6.0

A free local research desk: start with a company, inspect the public evidence, test valuation assumptions and save what would change your mind.

```bash
python3 scripts/investor.py desk
```

Open the printed local URL. Inspect frozen Microsoft, Coca-Cola and Caterpillar SEC financial histories offline, or fetch a supported US nonfinancial company by name. Python 3.9+, no model API, project account or pip dependencies for the desk. AI services, if used, have their own fees.

- Three reviewed-input models: equity DCF with reverse growth, normalized earning power, and common-equity residual income.
- Sensitivity chart/table, explicit assumptions, a thesis/counterevidence/catalyst notebook and export/restore. Valuation examples use hypothetical prices and illustrative cash assumptions, not verified company fair values.
- Optional real AhaSignals PIT checker integration: missing package remains UNKNOWN. Declared frozen financial forecast review is separate from a return backtest.
- Fixed a live-case extraction failure when annual net-income tags change; conflicting annual period starts remain withheld. Source capture now distinguishes missing issuer history from unsupported sectors.
- English/Chinese instructions and updated Japanese, Korean, German, French and Spanish guides. Both archives include the desk assets and calculation tools.

[Three-company walkthrough](https://github.com/AhaSignals/value-investor-skill/blob/v0.6.0/docs/research-desk.md) · [Formulas and boundaries](https://github.com/AhaSignals/value-investor-skill/blob/v0.6.0/references/valuation-desk.md) · [AhaSignals guide](https://ahasignals.com/value-investor-skill/desk/)

Downloads: `value-investor-skill-upload-v0.6.0.zip` for skill upload; `value-investor-skill-v0.6.0.zip` for source and tests; `SHA256SUMS` verifies both. Existing scanner schema 1.1.0 and event-scenario schema 0.1.0 are unchanged.

中文：新增免费本地投研工作台。查看三家公司的真实财务摘录，复核假设后计算 DCF、归一化盈利能力或银行剩余收益，保存观点、反证与下次核查事项。真实财务数据与示意估值假设严格分开；缺失字段保持未知。不提供投资建议、自动交易或已验证收益回测。
