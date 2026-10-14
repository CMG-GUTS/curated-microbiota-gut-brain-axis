from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from curated_microbiota_gut_brain_axis._data import FILES, validate
SOURCE = "https://raw.githubusercontent.com/CMG-GUTS/mllabiome/ba8890e06bc6482c308418e4e279c8074589933a/examples/data/GUTBRAIN"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    parser.add_argument("--version", default="gutbrain-v1")
    args = parser.parse_args()
    root = args.destination / "gutbrain"
    root.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if args.source is None:
            with urlopen(f"{SOURCE}/{name}", timeout=90) as response:
                content = response.read()
        else:
            content = (args.source / name).read_bytes()
        (root / name).write_bytes(content)
    stats = validate(root)
    manifest = {
        "schema": 1,
        "version": args.version,
        "files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FILES},
        "counts": stats,
    }
    (args.destination.parent / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"destination": str(root), "counts": stats}, sort_keys=True))


if __name__ == "__main__":
    main()
