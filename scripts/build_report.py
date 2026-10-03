#!/usr/bin/env python3
"""Generate a draft or final-candidate PDF; release is a separate user-approved step."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from artifact_checks import record_build, recorder_dependencies


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
    (experiment / "report" / "meta.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--mode", choices=("skeleton", "draft", "candidate"), default="draft")
    args = parser.parse_args()

    root = repo_root()
    experiment = args.experiment.resolve()
    if not (experiment / "report" / "main.tex").is_file():
        parser.error(f"not an experiment directory: {experiment}")

    generate_meta(experiment)
    required_phase = 7 if args.mode == "candidate" else (5 if args.mode == "skeleton" else 6)
    subprocess.run(
        [sys.executable, str(root / "scripts" / "validate_experiment.py"), str(experiment), "--phase", str(required_phase), *(["--draft"] if args.mode == "draft" else [])],
        cwd=root,
        check=True,
    )

    report_dir = experiment / "report"
    build_dir = experiment / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "report-mode.tex").write_text(
        f"\\def\\reportskeleton{{{1 if args.mode == 'skeleton' else 0}}}\n",
        encoding="utf-8",
        newline="\n",
    )
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
        # IfFileExists can introduce new prose files absent from the previous
        # recorder. Always rerun TeX rather than reusing a cached partial draft.
        "-g",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-recorder",
        f"-outdir={build_dir}",
        "main.tex",
    ]
    print("PDFを生成しています。初回はフォント準備のため数分かかることがあります。")
    result = subprocess.run(
        command,
        cwd=report_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    latexmk_output = build_dir / "latexmk-output.log"
    latexmk_output.write_bytes(result.stdout)
    if result.returncode != 0:
        tail = result.stdout.decode(errors="replace").splitlines()[-25:]
        raise RuntimeError(
            "PDF生成に失敗しました。詳細は build/latexmk-output.log を確認してください。\n"
            + "\n".join(tail)
        )

    pdf = build_dir / "main.pdf"
    log = build_dir / "main.log"
    if log.is_file():
        log_text = log.read_text(encoding="utf-8", errors="replace")
        fatal_warnings = {
            "undefined references": r"LaTeX Warning: There were undefined references",
            "undefined citations": r"LaTeX Warning: There were undefined citations",
            "multiply-defined labels": r"multiply defined",
            "overfull boxes": r"Overfull \\hbox|Overfull \\vbox",
        }
        found = [name for name, pattern in fatal_warnings.items() if re.search(pattern, log_text, re.I)]
        if found:
            raise RuntimeError(f"TeX quality warnings must be resolved: {', '.join(found)}")

    names = {
        "skeleton": "skeleton.pdf",
        "draft": "draft.pdf",
        "candidate": "final-candidate.pdf",
    }
    output = build_dir / names[args.mode]
    shutil.copy2(pdf, output)
    record_build(experiment, args.mode, output, recorder_dependencies(experiment))
    print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
