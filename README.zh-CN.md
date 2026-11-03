# value-investor-skill

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md)

## 这只股票，值现在这个价吗？

**适用于 Claude、GPT 和 DeepSeek 的价值投资研究 skill：看懂业务、检查估值、寻找反证，并在证据变化时更新原判断。**

一个 skill，五种研究流程。从公司名称或一个问题开始。普通聊天可直接复制研究指令；在支持工具的助手中安装完整技能，即可运行可复核的计算、保存研究版本。

**免费、MIT 开源、不需要注册项目账号。** AI 服务本身的账号、工具权限和费用仍适用。

[30 秒在线演示](https://ahasignals.com/value-investor-skill/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=zh_demo) · [选择你的助手](docs/hosts.md) · [English](README.md) · [AhaSignals 出品](https://ahasignals.com)

## 用你已经在用的助手开始

| 你使用的产品 | 最快入口 |
| --- | --- |
| **Claude、ChatGPT、DeepSeek 聊天** | 把[这份完整中文指令](prompts/START_HERE.zh-CN.md)复制到新对话，再输入公司名称。无需终端。 |
| **已启用 Skills 的 Claude** | 上传[技能 ZIP](https://github.com/AhaSignals/value-investor-skill/releases/download/v0.2.1/value-investor-skill-upload-v0.2.1.zip)，在 Customize → Skills 中启用。 |
| **Claude Code** | 输入下方两条插件命令。 |
| **使用 GPT 的 Codex** | 请它把本仓库安装为 skill；或使用下方 Python 安装器。 |
| **使用 DeepSeek 的技能宿主** | 按已配置的 Claude Code / Codex 宿主安装。[说明](docs/hosts.md#deepseek-chat-or-a-configured-skill-host)。 |

在 Claude Code 内输入：

```text
/plugin marketplace add AhaSignals/value-investor-skill
/plugin install value-investor@value-investor-skill
```

然后问：

> 用虚构的 40 美元股票给我演示：改一个估值假设，再撤回支撑它的证据，解释结果为什么改变。

研究真实公司时：

> 研究一下[公司名称]。它靠什么赚钱？当前股价要求哪些假设成立？什么证据会让我改变判断？

助手负责理解资料和解释；有执行权限和可写文件时，Python 负责情景计算和版本记录。普通聊天可以采用相同研究方法，但不会仅凭提示词建立持久账本。不能联网时，请提供原始资料。[能力说明与排错](docs/hosts.md)。

![虚构的40美元股票：同一价格，不同假设](assets/demo.svg)

<details>
<summary>习惯用终端？一分钟运行完整离线演示。</summary>

Python 3.9+。虚构演示不需要 pip 依赖、API key 或模型调用。

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/doctor.py
python3 scripts/investor.py demo --out output/first-demo
```

打开 `output/first-demo/before/research.html`，再打开 `output/first-demo/after/research.html`。重跑请换一个输出目录。Windows 可把 `python3` 换成 `py -3`。

复制安装：`python3 scripts/install.py --host codex` 或 `--host claude`。仅用于一个项目时，加 `--scope project --project ./my-project`。安装器保留已有安装。

也可使用[skills CLI](https://github.com/vercel-labs/skills)（Node.js 22.20+）：`npx skills add AhaSignals/value-investor-skill --skill value-investor-skill`。选择一种安装方式即可；设置 `DISABLE_TELEMETRY=1` 可关闭该 CLI 的遥测。

</details>

## 五个问题

| 你想知道 | 得到什么 |
| --- | --- |
| 公司靠什么赚钱？ | 业务说明、资金需求、真正影响价值的事件 |
| 不同结果下值多少？ | 现金、债务、成本、融资与稀释明确的估值情景 |
| 现在的价格要求什么？ | 支撑现价的多组假设，不强造唯一概率 |
| 我忽略了什么？ | 反证、缺失资料、暂缓结论的原因 |
| 跟上次相比变了什么？ | 新证据、受影响估值、保留下来的旧版本 |

业务判断与来源审查由助手或研究者完成。CLI 不会独立发现公司真实价值，也不会生成已验证的成功概率。具体方法见[研究协议](references/research-protocol.md)。

## 40美元的例子

*以下全部是假设数据，情景值为假设的每股现值。*

| 有利情景 | 不利情景 | 使加权价值等于40美元的有利情景权重 |
| ---: | ---: | ---: |
| 80美元 | 20美元 | 33.3% |
| 60美元 | 20美元 | 50.0% |

**哪些证据支持80美元，而不是60美元？** 这才是下一步要研究的问题。

两行是分别计算的二状态假设，不是成功概率或统计置信区间。示例随后撤回上市时间依据：两个依赖它的有利情景都变成 `NEEDS_REVIEW`，旧研究保留，新估值暂缓。[查看完整演示](docs/demo.md)。

## AhaSignals 的差异

- **价格与证据分开。** 股价变化不改变已输入的状态经济价值；研究协议禁止用价格反推想要的成功概率。
- **资料有时间。** 区分公开时间与实际观察时间；未来资料、撤回资料会阻断依赖它的估值。
- **融资同时影响现金和股数。** 不只计算筹到了多少钱，也计算新增股份。
- **更新留下历史。** SQLite 保存输入、输出与变更事件，新版本不覆盖旧判断。
- **不知道就明确说。** v0.1 不估计经过校准的概率或可执行价差；在情景计算之外保留 `NOT_ESTIMATED` 和 `NO_QUOTE`。

这些是可检查的功能和方法边界，不是盈利或优于所有其他研究工具的承诺。

## 用于自己的研究

复制示例结构，逐项替换为审查过的证据与假设，设 `fictional` 为 `false` 并提供真实来源 URL。不要把示例数字套在真实公司上。

```bash
python3 scripts/investor.py analyze my-research.json --out output/my-review
python3 scripts/investor.py freeze my-research.json --db output/my-ledger.sqlite
python3 scripts/investor.py verify --db output/my-ledger.sqlite
```

[完整字段、更新与历史命令](references/input-contract.md)。可选的 SEC 工具按 CIK 和受理时间筛选最近申报索引，需要组织/联系标识与网络；不声称覆盖全部历史资料，也不自动生成估值。

## 当前边界

已实现：技能安装、本地情景计算、条件式二状态反演、资料时间与依赖检查、版本账本、修订比较、HTML/Markdown/JSON 报告、假设临床与并购案例、可选 SEC 索引发现。

尚不提供：经过校准的临床模型、全市场自动研究、完整 DCF、把假设情景当统计分布、组合配置建议、持续监控、交易执行或已验证 alpha。临床与简单现金并购有专项研究清单；其他公司需要合适的自定义模型。

程序不验证声明的来源是否真实，不消除模型预训练中的未来知识，也不保证本地数据库管理员无法改写历史。第三方数据使用权与代码许可证分开。

## 验证与参与

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_public_identity.py
python3 scripts/package_release.py --out dist
```

测试覆盖计算、稀释、时间截点、陈旧价格、资料失效、版本冲突、重复事件、恢复、改写检测和独立安装；不证明投资收益。[贡献方式](CONTRIBUTING.md) · [安全说明](SECURITY.md) · [版本记录](CHANGELOG.md)

欢迎提交可复现且已去除私人信息的案例。不要在 issue 上传私人持仓、凭证或无权公开的原始文件。

AhaSignals 是独立研究发布者。本项目仅供研究与教育，不构成投资、交易、法律、税务或医疗建议；第三方名称仅作来源或兼容说明，不表示合作或背书。代码与原创假设数据采用 MIT 许可，第三方来源权利不由该许可授予。

后续开发方向见 [Roadmap](docs/roadmap.md)；中英文发布文案见 [Launch kit](docs/launch-kit.md)。开源工具无需 AhaSignals 账号，v0.1 不会自动上传研究资料。

## 继续阅读 AhaSignals

[查看有来源和日期的现金流案例](https://ahasignals.com/research/rebalance-cash-review/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=zh_case)，或[了解资料时间与修订方法](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=zh_methodology)。[多语言范围与翻译贡献](docs/translations.md)。
