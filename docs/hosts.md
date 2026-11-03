# Choose your assistant

**Model names and skill hosts are different.** Claude, GPT and DeepSeek supply reasoning. The app decides whether it can install a skill, browse, execute Python and retain files. This project makes no API calls and does not change your provider, credentials or permissions.

| Where you work | Fastest start | What you get |
| --- | --- | --- |
| Claude, ChatGPT or DeepSeek chat | Copy [English](../prompts/START_HERE.md) or [中文](../prompts/START_HERE.zh-CN.md) into a new chat | Five research workflows; tools depend on your chat session |
| Claude with custom skills enabled | Upload the **upload ZIP** from [Releases](https://github.com/AhaSignals/value-investor-skill/releases/latest) | Skill instructions and bundled Python tools where execution is available |
| Claude Code | Two plugin commands below, or the Python installer | Local research, calculations and saved revisions |
| GPT in Codex | Ask Codex to install this repository as a skill, or use the Python installer | The same local research and calculation tools |
| DeepSeek in Claude Code or Codex | Configure the host using DeepSeek's documentation, then use that host's installation route | Same files and Python engine; model quality and tool access depend on the configured host |
| Other chat assistants | Use the portable instructions | Text workflow; no claim of a tested native integration |

## No installation: ordinary chat

1. Copy [the complete portable instructions](../prompts/START_HERE.md) into a new conversation. [中文版本](../prompts/START_HERE.zh-CN.md).
2. Send: **“Show me the fictional $40 example.”** Then try **“Research [company]. What does its price assume?”**
3. When browsing is unavailable, supply filings or excerpts. When execution is unavailable, the assistant should show formulas and label calculations as not engine-verified. Save the chat yourself; prompt mode does not create the SQLite ledger.

You can use the same text as custom instructions in an assistant that accepts them. An attached file alone may not activate a skill; explicitly ask the assistant to follow it. Do not paste credentials or private brokerage records.

## Claude Code: plugin

Run these **inside Claude Code**, not in your system shell:

```text
/plugin marketplace add AhaSignals/value-investor-skill
/plugin install value-investor@value-investor-skill
```

Reload plugins or start a new session. Ask **“Use Value Investor to show the fictional $40 demo.”** The namespaced command is `/value-investor:value-investor-skill`.

For updates, use `/plugin` to update the installed plugin. A plugin installation and a copied personal skill are separate installations; choose one route to avoid duplicate entries. This marketplace is maintained by AhaSignals and is not an official Anthropic listing. See [Claude's marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces) and [manifest reference](https://code.claude.com/docs/en/plugins-reference).

## Claude web / desktop: upload

Download `value-investor-skill-upload-v0.2.0.zip` from [the release](https://github.com/AhaSignals/value-investor-skill/releases/tag/v0.2.0). Keep the ZIP intact. In Claude, use **Customize → Skills → Create skill → Upload a skill**, then enable it. Code execution must be available for the Python workflow. Ask for the fictional demo and save its generated files if you need them later. Cloud sessions do not automatically retain a local ledger across chats. [Claude's current instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## GPT / Codex: local skill

Paste this into Codex with repository and filesystem access:

```text
Install https://github.com/AhaSignals/value-investor-skill as a skill for this app.
Read docs/hosts.md, preserve any existing installation, then show the fictional $40 demo.
```

Or clone/download and extract the **source ZIP**, then run:

```bash
python3 scripts/install.py --host codex
```

It installs in `~/.agents/skills/value-investor-skill`. Type `$value-investor-skill` or choose it from `/skills`. Existing v0.1 installations in `~/.codex/skills` are preserved; back up and move the old copy before installing in the current location. See [OpenAI's local skill documentation](https://learn.chatgpt.com/docs/build-skills).

**ChatGPT chat is a separate route.** Use the portable instructions immediately. If your workspace exposes custom skill upload, use the upload ZIP through its skill controls. Availability and permissions depend on the account; installing a local Codex skill does not install a workspace Skill. This repository has not been published to the OpenAI plugin directory. [OpenAI's distribution boundaries](https://learn.chatgpt.com/docs/enterprise/skills).

## DeepSeek: chat or a configured skill host

For DeepSeek chat, use the portable instructions above. For executable tools, DeepSeek documents integrations with [Claude Code](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/) and [Codex](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/). Follow the provider's current setup in the host you already use, then install this skill for **that host**. A DeepSeek API key and usage charges may apply. Browsing is a separate host/provider capability.

The installer does not create a fictitious `.deepseek/skills` directory or change model configuration. Never put a provider key into this repository, a research bundle or a public issue. We have not run a paid DeepSeek session or certified equal research quality across models.

## Manual installation, project scope and checks

From a cloned repository or extracted **source ZIP**:

```bash
python3 scripts/install.py                         # interactive app chooser
python3 scripts/install.py --host claude           # personal Claude Code skill
python3 scripts/install.py --host codex --scope project --project ./my-project
python3 scripts/doctor.py                         # local package/runtime check
python3 scripts/investor.py demo --out output/first-demo
```

On Windows use `py -3` in place of `python3`. No pip dependencies. Project scope uses `.claude/skills` or `.agents/skills` below the chosen project. `--target` accepts a custom parent skill directory. Existing installations are never overwritten. Installation does not install Python, an AI app, a model or browsing tools.

Open `output/first-demo/before/research.html` and `output/first-demo/after/research.html`. Repeating the demo requires a new output directory; it will not overwrite saved research. If your host reports a missing skill, start a new session and check which installation scope it loads. If Python is missing, use the browser demo or portable prompt now and install Python separately when you need reproducible calculations.

## Compatibility evidence

Checked against the official documentation on **2026-11-04**. Automated tests cover source/upload ZIP extraction, copied installation, current host paths, preserved existing files and local demo execution. Claude Code CLI 2.1.317 validated both manifests and installed the plugin into an isolated test configuration; its component inventory found the skill, and the installed copy passed the offline demo. These checks establish packaging and local execution, not successful account-specific upload or model reasoning quality. The release does not include a paid provider benchmark. [Report a reproducible problem](https://github.com/AhaSignals/value-investor-skill/issues/new?template=experience.yml).

AhaSignals is independent. Product names indicate compatibility and source context, without affiliation or endorsement. Research and education only.
