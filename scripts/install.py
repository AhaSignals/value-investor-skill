#!/usr/bin/env python3
"""Install the research skill in a supported host without editing model settings."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PARTS = ("SKILL.md", "agents", "core", "scripts", "references", "examples", "assets", "docs", "prompts", "tests",
         "README.md", "README.zh-CN.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "AGENTS.md")
PARTS += tuple("README." + locale + ".md" for locale in ("ja", "ko", "de", "fr", "es"))


def destination(host, scope, project, home):
    base = project if scope == "project" else home
    return base / (".agents" if host == "codex" else ".claude") / "skills" / "value-investor-skill"


def install(dest, root=ROOT):
    # A dangling symlink is also an existing installation. Never follow it.
    if os.path.lexists(dest):
        raise ValueError("Installation already exists. Keep or move it before installing a new copy.")
    if any(not (root / name).exists() for name in PARTS):
        raise ValueError("Incomplete source package. Extract the full source ZIP or clone the repository, then retry.")
    for name in PARTS:
        source = root / name
        if source.is_symlink() or (source.is_dir() and any(p.is_symlink() for p in source.rglob('*'))):
            raise ValueError("Source package contains a symbolic link; use a complete release copy.")
    dest.mkdir(parents=True, exist_ok=False)
    for name in PARTS:
        source = root / name
        if source.is_dir():
            shutil.copytree(source, dest / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(source, dest / name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--host", choices=("codex", "claude"), help="Choose the app that loads the skill, not the model provider")
    group.add_argument("--target", type=Path, help="Custom parent skill directory; existing copies are preserved")
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project", type=Path, help="Project root (requires --scope project); otherwise uses the current directory")
    args = parser.parse_args(argv)
    if args.target and (args.scope != 'user' or args.project):
        parser.error('--target cannot be combined with project scope')
    if args.project and args.scope != 'project':
        parser.error('--project requires --scope project')
    if not args.host and not args.target:
        print("Choose the app that will run the skill:\n  1  Claude Code (Claude or a configured compatible model)\n  2  Codex (GPT or a configured compatible model)\n  3  ChatGPT / Claude / DeepSeek chat: open prompts/START_HERE.md")
        if not sys.stdin.isatty():
            print("No files changed. Run with --host claude or --host codex, or copy the portable instructions.")
            return 0
        try:
            choice = input("Choice [1/2/3]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 2
        if choice == '3':
            print("Copy prompts/START_HERE.md (or START_HERE.zh-CN.md) into your chat. No installation needed.")
            return 0
        args.host = {'1': 'claude', '2': 'codex'}.get(choice)
        if not args.host:
            print("No valid host selected; no files changed.", file=sys.stderr)
            return 2
    home = Path.home()
    if args.host == 'codex' and args.scope == 'user':
        legacy = home / '.codex/skills/value-investor-skill'
        if os.path.lexists(legacy):
            print("A legacy Codex installation exists in ~/.codex/skills/value-investor-skill. Keep it, or back it up and move it before using the current ~/.agents/skills location. No files changed.", file=sys.stderr)
            return 2
    dest = args.target.expanduser() / 'value-investor-skill' if args.target else destination(args.host, args.scope, (args.project or Path.cwd()).expanduser(), home)
    try:
        install(dest)
    except (OSError, ValueError) as error:
        print(str(error) if isinstance(error, ValueError) else "Installation failed. Inspect the target for a partial copy before retrying.", file=sys.stderr)
        return 2
    print("Installed value-investor-skill. Reload your host's skills or start a new session.")
    print('First message: Use value-investor-skill. Show the fictional $40 demo and explain what changes when its supporting evidence is withdrawn.')
    print('Optional setup check: run scripts/doctor.py from the installed skill directory.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
