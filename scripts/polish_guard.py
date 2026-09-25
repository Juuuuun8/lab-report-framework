#!/usr/bin/env python3
"""Protect technical tokens while a language editor polishes report prose."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


PROTECTED_ENVIRONMENTS = ("equation", "align", "align*", "figure", "table", "lstlisting")
TOKEN_PATTERNS = (
    r"https?://[^\s}\]]+",
    r"\\(?:ref|eqref|pageref|label|cite|sourcecite)\{[^}]+\}",
    r"\\[A-Za-z@]+\*?",
    r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?",
    r"\b(?:ms|ns|s|Hz|kHz|MHz|GHz|B|KB|MB|GB|V|mV|A|mA|W|mW|m|cm|mm|kg|g|K|degC|%)\b",
)


def protected_snapshot(report: Path) -> dict:
    files = sorted((report / "sections").glob("*.tex"))
    snapshot: dict[str, dict] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        tokens: list[str] = []
        for pattern in TOKEN_PATTERNS:
            tokens.extend(re.findall(pattern, text))
        environments: list[str] = []
        for env in PROTECTED_ENVIRONMENTS:
            pattern = re.compile(rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}", re.S)
            environments.extend(hashlib.sha256(match.group(0).encode()).hexdigest() for match in pattern.finditer(text))
        snapshot[path.name] = {
            # JSON has arrays rather than tuples; emit lists so a loaded
            # baseline compares identically to a fresh in-memory snapshot.
            "tokens": [list(item) for item in sorted(Counter(tokens).items())],
            "environment_hashes": sorted(environments),
        }
    return snapshot


def baseline_path(experiment: Path) -> Path:
    return experiment / "quality" / "POLISH_BASELINE.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("snapshot", "verify"))
    parser.add_argument("experiment", type=Path)
    args = parser.parse_args()
    experiment = args.experiment.resolve()
    report = experiment / "report"
    if not (report / "main.tex").is_file():
        parser.error(f"not an experiment directory: {experiment}")

    current = protected_snapshot(report)
    baseline = baseline_path(experiment)
    if args.mode == "snapshot":
        baseline.parent.mkdir(exist_ok=True)
        baseline.write_text(
            json.dumps(current, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(baseline)
        return 0

    if not baseline.is_file():
        print("FAIL: polish baseline does not exist; run snapshot before editing", file=sys.stderr)
        return 1
    expected = json.loads(baseline.read_text(encoding="utf-8"))
    if current == expected:
        print("PASS: protected technical tokens are unchanged")
        return 0

    print("FAIL: protected technical content changed", file=sys.stderr)
    for name in sorted(set(expected) | set(current)):
        if expected.get(name) != current.get(name):
            print(f"- {name}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
