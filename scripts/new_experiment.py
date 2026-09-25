#!/usr/bin/env python3
"""Create one experiment workspace from the canonical template."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id", help="lowercase letters, digits, and hyphens")
    parser.add_argument("--title", required=True, help="experiment title")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.experiment_id):
        parser.error("experiment_id must use lowercase letters, digits, and hyphens")

    root = Path(__file__).resolve().parents[1]
    source = root / "templates" / "experiment"
    target = root / "experiments" / args.experiment_id
    if target.exists():
        parser.error(f"already exists: {target}")

    shutil.copytree(source, target)
    meta_path = target / "spec" / "REPORT_META.yaml"
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    meta["cover"]["title"] = args.title
    meta_path.write_text(
        yaml.safe_dump(meta, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(target.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

