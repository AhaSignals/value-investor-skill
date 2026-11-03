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


def build(out):
    if inspect():
        raise ValueError("Source identity check failed")
    out.mkdir(parents=True, exist_ok=True)
    archive = out / ("value-investor-skill-v" + __version__ + ".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in public_files():
            info = zipfile.ZipInfo("value-investor-skill/" + path.relative_to(ROOT).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, path.read_bytes(), compresslevel=9)
    if inspect(archive=archive):
        archive.unlink()
        raise ValueError("Archive identity check failed")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out / "SHA256SUMS").write_text(checksum + "  " + archive.name + "\n", encoding="utf-8")
    print(archive.name + " · SHA-256 " + checksum)
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
