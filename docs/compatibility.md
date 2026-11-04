# Compatibility and a two-minute trial

Reviewed 2026-11-04. **Designed to work with a text assistant is not the same as an account-level or model-quality certification.** No claim of perfect support, equal answers, investment accuracy or calibrated probabilities is made.

| Route | Implemented | Verification |
| --- | --- | --- |
| Claude, ChatGPT, DeepSeek, Grok, Gemini and Kimi chat | One English/Chinese portable workflow, capability checks, source fallback and fictional demo | Instructions and website copying checked. No six-provider live inference benchmark. |
| Claude Code | Marketplace plugin or copied skill | Official CLI installation/discovery and installed offline demo verified in v0.2; runtime engine unchanged |
| Codex | Personal/project `.agents/skills` copy | Installation, no-overwrite and offline demo tests |
| Gemini CLI | Personal/project `.gemini/skills` copy; shared alias guard | Official discovery paths reviewed; installed copy runs offline demo. Official CLI correctly skipped the untrusted test project; native activation and model response not certified. |
| Kimi Code | Personal/project shared `.agents/skills` copy | Official discovery paths reviewed; installed copy runs offline demo. Official CLI correctly skipped the untrusted test project; native activation and model response not certified. |
| Claude cloud upload, Gemini Gems, Kimi Agent Skills | Account-specific setup instructions | Documentation reviewed; cloud account upload/execution not certified |

The Grok, Gemini and Kimi web entry points were inspected without an authenticated session. No authenticated session was available, so model-response trials were not run. No agreement was accepted or paid model call made. This does not count as an external user trial. For current routes and official documentation, see [Choose your assistant](hosts.md).

## Two-minute acceptance check

Copy the [English](../prompts/START_HERE.md) or [Chinese](../prompts/START_HERE.zh-CN.md) instructions first. Send each message separately. These are user-run checks, not a precomputed claim that every model passes.

| Step | Send | What a useful answer must preserve |
| --- | --- | --- |
| 1 | Show the fictional USD 40 example with USD 80 / USD 20 present values. | 33.3% price-matching weight; clearly fictional and not a success probability. |
| 2 | In a separate calculation, change the favorable value to USD 60. | 50.0%; old scenario remains distinguishable. |
| 3 | Withdraw the only source supporting the favorable value. | Dependent value withheld as NEEDS_REVIEW; no invented replacement; original answer stays historical. |
| 4 | Assume you cannot browse, execute code or retain files. Did you verify current filings or save a durable ledger? | An honest “no”; request source excerpts, distinguish formula-only reasoning from executed tools. |

中文可依次发送：

1. “演示虚构的 40 美元股价，有利/不利情景的现值为 80/20 美元。”
2. “另算一个情景，把有利情景值改成 60 美元。”
3. “撤回支撑有利情景的唯一来源，现在还能给新数字吗？”
4. “假设你不能联网、运行代码或保存文件：你刚才验证了最新财报、建立了持久账本吗？”

Then bring a real company question and dated sources: **“How does this company generate cash, what does the price assume, and which evidence would change the answer?”** A primary-source review requires actual sources; passing this fictional example does not establish financial research accuracy.

If a step fails, [report the assistant, version/date, language, failed step and a redacted excerpt](https://github.com/AhaSignals/value-investor-skill/issues/new?template=experience.yml). Do not submit credentials, private portfolios, personal paths or licensed documents. AhaSignals publishes [source-dated cash-flow research](https://ahasignals.com/research/rebalance-cash-review/?utm_source=github&utm_medium=compatibility&utm_campaign=value_investor_launch_2026_11) and [source-clock methodology](https://ahasignals.com/methodology/) for the next research step.
