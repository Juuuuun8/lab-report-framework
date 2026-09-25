#!/usr/bin/env python3
"""Render every PDF page to PNG for the mandatory visual review."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(args.pdf)
    matrix = fitz.Matrix(args.dpi / 72, args.dpi / 72)
    for index, page in enumerate(document, 1):
        output = args.output_dir / f"page-{index:02d}.png"
        page.get_pixmap(matrix=matrix, alpha=False).save(output)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

