#!/usr/bin/env python3
"""Render every PDF page to PNG for the mandatory visual review."""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
from pathlib import Path

import pymupdf
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--manifest", type=Path, help="write hashes proving which PDF and page images were reviewed")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.manifest:
        try:
            args.output_dir.resolve().relative_to(args.manifest.resolve().parent)
        except ValueError as exc:
            parser.error("output_dir must be inside the manifest's parent directory")
    document = pymupdf.open(args.pdf)
    matrix = pymupdf.Matrix(args.dpi / 72, args.dpi / 72)
    pages = []
    for index, page in enumerate(document, 1):
        output = args.output_dir / f"page-{index:02d}.png"
        page.get_pixmap(matrix=matrix, alpha=False).save(output)
        print(output)
        pages.append({
            "path": (
                output.resolve().relative_to(args.manifest.resolve().parent).as_posix()
                if args.manifest
                else output.as_posix()
            ),
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "bytes": output.stat().st_size,
        })
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "source_sha256": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
            "rendered_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "dpi": args.dpi,
            "page_count": len(pages),
            "pages": pages,
        }
        args.manifest.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
            newline="\n",
        )
        print(args.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
