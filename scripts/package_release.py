#!/usr/bin/env python3
"""Build a deterministic source ZIP with neutral metadata and a SHA-256 sum."""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

from check_public_identity import ROOT, inspect, public_files

sys.path.insert(0, str(ROOT))
from core import __version__


def upload_files():
    allowed = {"SKILL.md", "LICENSE", "core", "references", "examples", "prompts", "agents"}
    runtime_scripts = {"investor.py", "fetch_sec.py", "doctor.py"}
    for path in public_files():
        rel = path.relative_to(ROOT)
        if rel.parts[0] in allowed or (rel.parts[0] == "scripts" and path.name in runtime_scripts):
            yield path


def write_archive(archive, files):
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in files:
            info = zipfile.ZipInfo("value-investor-skill/" + path.relative_to(ROOT).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, path.read_bytes(), compresslevel=9)
    if inspect(archive=archive):
        archive.unlink()
        raise ValueError("Archive identity check failed")
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def build(out):
    if inspect():
        raise ValueError("Source identity check failed")
    out.mkdir(parents=True, exist_ok=True)
    archive = out / ("value-investor-skill-v" + __version__ + ".zip")
    checksum = write_archive(archive, public_files())
    upload = out / ("value-investor-skill-upload-v" + __version__ + ".zip")
    upload_checksum = write_archive(upload, upload_files())
    (out / "SHA256SUMS").write_text(checksum + "  " + archive.name + "\n" + upload_checksum + "  " + upload.name + "\n", encoding="utf-8")
    print(archive.name + " · SHA-256 " + checksum)
    print(upload.name + " · SHA-256 " + upload_checksum)
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        build(args.out)
    except (OSError, ValueError) as error:
        print("Release build failed: " + (str(error) if isinstance(error, ValueError) else "file access error"), file=sys.stderr)
        sys.exit(2)
