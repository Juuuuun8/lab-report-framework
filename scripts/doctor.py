#!/usr/bin/env python3
"""Check whether this clone is ready for a reliable report workflow."""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(label: str, argv: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        print(f"OK  {label}")
        return True, ""
    detail = (result.stdout + result.stderr).strip()
    print(f"NG  {label}")
    return False, detail


def main() -> int:
    parser = argparse.ArgumentParser(description="ローカル環境と完成例を診断します。")
    parser.add_argument("--quick", action="store_true", help="回帰テストを省き、依存関係だけ確認する")
    args = parser.parse_args()

    failures: list[str] = []
    if sys.version_info < (3, 10):
        failures.append("Python 3.10以上が必要です。")
        print("NG  Python 3.10以上")
    else:
        print(f"OK  Python {sys.version_info.major}.{sys.version_info.minor}")

    for module in ("yaml", "jsonschema", "pypdf", "pymupdf"):
        try:
            importlib.import_module(module)
            print(f"OK  Python依存: {module}")
        except ImportError:
            failures.append(f"Python依存がありません: {module}（requirements.txtを導入してください）")
            print(f"NG  Python依存: {module}")

    for command in ("latexmk", "lualatex"):
        if shutil.which(command):
            print(f"OK  PDF生成: {command}")
        else:
            failures.append(f"PDF生成コマンドがありません: {command}（TeX Liveを導入してください）")
            print(f"NG  PDF生成: {command}")

    if not args.quick and not failures:
        checks = [
            (
                "回帰テスト",
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            ),
            (
                "完成例の再現性",
                [sys.executable, "scripts/reproduce.py", "verify", "examples/sort-benchmark"],
            ),
            (
                "完成例の承認状態",
                [sys.executable, "scripts/workflow.py", "verify", "examples/sort-benchmark"],
            ),
            (
                "完成例の最終検査",
                [sys.executable, "scripts/validate_experiment.py", "examples/sort-benchmark", "--phase", "8"],
            ),
        ]
        for label, argv in checks:
            ok, detail = run(label, argv)
            if not ok:
                failures.append(f"{label}:\n{detail}")

    if failures:
        print("\n診断結果: 修正が必要です。", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    suffix = "（簡易）" if args.quick else ""
    print(f"\n診断結果: 利用可能です{suffix}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
