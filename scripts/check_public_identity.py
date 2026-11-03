#!/usr/bin/env python3
"""Inspect publishable source and archive bytes without printing matched data."""
import argparse
import getpass
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {"README.md", "README.zh-CN.md", "SKILL.md", "LICENSE", "AGENTS.md",
         "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", ".gitignore", ".gitattributes"}
FILES.update("README." + locale + ".md" for locale in ("ja", "ko", "de", "fr", "es"))
DIRECTORIES = {"core", "scripts", "tests", "examples", "references", "assets", "agents", "docs", ".github"}


def public_files(root=ROOT):
    for path in sorted(root.rglob("*")):
        parts = path.relative_to(root).parts
        if parts[0] not in FILES | DIRECTORIES or any(p in {"__pycache__", ".DS_Store"} for p in parts):
            continue
        if path.is_symlink():
            raise ValueError("Publishable tree contains a symbolic link")
        if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
            yield path


def findings(data):
    value = data.decode("utf-8", errors="replace")
    issues = []
    patterns = (r"/" + r"(?:Users|home)/[A-Za-z0-9_.-]+/", r"[A-Za-z]:[\\/]" + r"Users[\\/][^\s\\/]+[\\/]")
    if any(re.search(pattern, value) for pattern in patterns):
        issues.append("personal machine path")
    for email in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", value):
        if not email.lower().endswith("@ahasignals.com"):
            issues.append("non-organizational email requires review")
    operator = getpass.getuser()
    if len(operator) >= 3 and operator.lower() not in {"researcher", "runner", "root", "ahasignals"}:
        if re.search(r"(?i)(?:author|operator|publisher|created_by)\s*[=:]\s*[\"']?" + re.escape(operator) + r"\b", value):
            issues.append("personal operator attribution")
    return sorted(set(issues))


def inspect(root=ROOT, archive=None):
    errors = []
    for path in public_files(root):
        issues = findings(path.read_bytes()) + findings(path.relative_to(root).as_posix().encode())
        if issues:
            errors.append((path.relative_to(root).as_posix(), sorted(set(issues))))
    if archive:
        with zipfile.ZipFile(archive) as package:
            for info in package.infolist():
                issues = findings(package.read(info)) + findings(info.filename.encode()) + findings(info.extra + info.comment)
                if issues:
                    errors.append(("archive member", sorted(set(issues))))
            if findings(package.comment) or findings(Path(archive).read_bytes()):
                errors.append(("archive metadata", ["identity pattern in binary content"]))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    try:
        errors = inspect(archive=args.archive)
    except (OSError, ValueError, zipfile.BadZipFile):
        print("Identity check could not inspect all requested files", file=sys.stderr)
        return 2
    for name, issues in errors:
        print(name + ": " + ", ".join(issues), file=sys.stderr)
    if errors:
        return 1
    print("Public identity check passed (source" + (" and archive bytes)" if args.archive else ")"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
