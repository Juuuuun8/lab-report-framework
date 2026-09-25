#!/usr/bin/env python3
"""Rebuild the fictional example's summaries and TeX table from raw timings."""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "timings.csv"
PROCESSED = ROOT / "data" / "processed"
GENERATED = ROOT / "report" / "generated"


def main() -> None:
    groups: dict[tuple[str, int], list[float]] = defaultdict(list)
    with RAW.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            groups[(row["algorithm"], int(row["n"]))].append(float(row["elapsed_ms"]))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    rows = []
    for (algorithm, n), values in sorted(groups.items(), key=lambda item: (item[0][1], item[0][0])):
        rows.append({
            "n": n,
            "algorithm": algorithm,
            "mean_ms": statistics.fmean(values),
            "sd_ms": statistics.stdev(values),
            "trials": len(values),
        })

    with (PROCESSED / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["n", "algorithm", "mean_ms", "sd_ms", "trials"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "mean_ms": f"{row['mean_ms']:.4f}", "sd_ms": f"{row['sd_ms']:.4f}"})

    for algorithm in ("bubble", "quick"):
        with (GENERATED / f"{algorithm}.dat").open("w", encoding="ascii", newline="") as stream:
            stream.write("n_thousands mean_ms\n")
            for row in rows:
                if row["algorithm"] == algorithm:
                    stream.write(f"{row['n'] / 1000:g} {row['mean_ms']:.4f}\n")

    by_key = {(row["n"], row["algorithm"]): row for row in rows}
    lines = [
        r"\begin{tabular}{rrrr}",
        r"\toprule",
        r"入力サイズ $n$ & バブルソート（ms） & クイックソート（ms） & 比率 \\",
        r"\midrule",
    ]
    row_end = " " + "\\" * 2
    for n in sorted({row["n"] for row in rows}):
        bubble = by_key[(n, "bubble")]["mean_ms"]
        quick = by_key[(n, "quick")]["mean_ms"]
        lines.append(f"{n:,} & {bubble:.2f} & {quick:.3f} & {bubble / quick:.1f}" + row_end)
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    (GENERATED / "summary_table.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
