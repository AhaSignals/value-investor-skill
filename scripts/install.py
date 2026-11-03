#!/usr/bin/env python3
"""Copy the self-contained skill without altering unrelated host configuration."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
PARTS = ("SKILL.md", "agents", "core", "scripts", "references", "examples", "assets", "docs", "tests",
         "README.md", "README.zh-CN.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", "AGENTS.md")

PARTS += tuple("README." + locale + ".md" for locale in ("ja", "ko", "de", "fr", "es"))

def main():
    parser = argparse.ArgumentParser(description="Install a copy. Existing installations are never overwritten.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--host", choices=("codex", "claude"))
    group.add_argument("--target", type=Path, help="Parent directory for a test or custom skill installation")
    args = parser.parse_args()
    parent = args.target if args.target else Path.home() / (".codex" if args.host == "codex" else ".claude") / "skills"
    dest = parent / "value-investor-skill"
    if dest.exists():
        print("Installation already exists. Keep or move it before installing a new copy.", file=sys.stderr)
        return 2
    try:
        dest.mkdir(parents=True)
        for name in PARTS:
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, dest / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                shutil.copy2(source, dest / name)
    except OSError:
        print("Installation failed; inspect the target directory before retrying.", file=sys.stderr)
        return 2
    print("Installed value-investor-skill. Restart or reload your agent's skills, then ask it to use the skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
