#!/usr/bin/env python3
"""Generate cover metadata, build the LuaLaTeX report, and collect deliverables."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


TEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "#": r"\#",
    "$": r"\$",
    "%": r"\%",
    "&": r"\&",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex_escape(value: object) -> str:
    return "".join(TEX_ESCAPES.get(char, char) for char in str(value))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def generate_meta(experiment: Path) -> None:
    data = yaml.safe_load((experiment / "spec" / "REPORT_META.yaml").read_text(encoding="utf-8"))
    cover = data["cover"]
    lines = [
        "% Generated from spec/REPORT_META.yaml. Do not edit directly.",
        rf"\reportcourse{{{tex_escape(cover['course_name'])}}}",
        rf"\reporttitle{{{tex_escape(cover['title'])}}}",
        rf"\reportsubtitle{{{tex_escape(cover.get('subtitle', ''))}}}",
    ]
    for field in cover["fields"]:
        lines.append(rf"\reportfield{{{tex_escape(field['label'])}}}{{{tex_escape(field['value'])}}}")
    (experiment / "report" / "meta.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=Path)
    args = parser.parse_args()

    root = repo_root()
    experiment = args.experiment.resolve()
    if not (experiment / "report" / "main.tex").is_file():
        parser.error(f"not an experiment directory: {experiment}")

    # A PDF must never be produced from an experiment that has not passed the
    # evidence, traceability, integrity, and style gates through PHASE 6.
    subprocess.run(
        [sys.executable, str(root / "scripts" / "validate_experiment.py"), str(experiment), "--phase", "6"],
        cwd=root,
        check=True,
    )

    generate_meta(experiment)
    report_dir = experiment / "report"
    build_dir = experiment / "build"
    deliverables = experiment / "deliverables"
    build_dir.mkdir(exist_ok=True)
    deliverables.mkdir(exist_ok=True)
    tex_cache = build_dir / "tex-cache"
    tex_cache.mkdir(exist_ok=True)

    env = os.environ.copy()
    env["TEXINPUTS"] = str(root / "tex") + os.pathsep + env.get("TEXINPUTS", "")
    # LuaTeX requires a writable font cache. Keeping it inside the experiment
    # also makes the build work in restricted or disposable environments.
    env["TEXMFCACHE"] = str(tex_cache)
    env["TEXMFVAR"] = str(tex_cache)
    command = [
        "latexmk",
        "-lualatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-outdir={build_dir}",
        "main.tex",
    ]
    subprocess.run(command, cwd=report_dir, env=env, check=True)

    pdf = build_dir / "main.pdf"
    shutil.copy2(pdf, deliverables / "report.pdf")
    for name in [
        "HANDOFF.md",
        "SOURCE_AUDIT.md",
        "RESULT_TRACEABILITY.md",
        "RUBRIC_TRACEABILITY.md",
        "ORAL_DEFENSE.md",
        "WORKLOG.md",
    ]:
        shutil.copy2(experiment / name, deliverables / name)
    shutil.copy2(experiment / "quality" / "QUALITY_REVIEW.yaml", deliverables / "QUALITY_REVIEW.yaml")
    print(deliverables / "report.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
