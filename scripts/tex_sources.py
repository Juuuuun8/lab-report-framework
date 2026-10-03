"""Read literal TeX inputs in document order, ignoring comments and unused files.

This is deliberately not a TeX interpreter. Dynamic input paths are rejected;
macro-generated layouts still require compilation and visual review.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


def strip_comments(text: str) -> str:
    # Verbatim code is data, not TeX; leave its percent signs intact.
    parts = re.split(r"(\\begin\{lstlisting\}.*?\\end\{lstlisting\})", text, flags=re.S)
    return "".join(part if part.startswith(r"\begin{lstlisting}") else re.sub(r"(?<!\\)%[^\n]*", "", part) for part in parts)


def document_text(experiment: Path, *, planned: bool = False, expand_prose: bool = True) -> str:
    report = experiment / "report"
    main = report / "main.tex"
    plan_path = experiment / "spec/WRITING_PLAN.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8")) if plan_path.is_file() else {}
    slots = {item["slot_id"]: item for item in (plan or {}).get("slots", [])}

    def expand(text: str, active: tuple[Path, ...], *, preamble: bool = False) -> str:
        pattern = r"\\(?:input|include)\{([^}]+)\}|\\proseslot\{(P-[0-9]{3})\}\{(文章[0-9]+)\}"
        def replace(match: re.Match) -> str:
            if match.group(1) is not None:
                raw = match.group(1)
                if preamble and (raw == "../build/report-mode.tex" or raw == "../prose/typeset/#1.tex"):
                    return match.group(0)  # The canonical runtime macros are inspected through slots below.
                if "\\" in raw or "#" in raw:
                    raise ValueError(f"dynamic TeX input is unsupported: {raw}")
                path = (report / raw).resolve()
                if not path.suffix:
                    path = path.with_suffix(".tex")
                path.relative_to(experiment.resolve())
                if path in active:
                    raise ValueError(f"recursive TeX input: {raw}")
                if not path.is_file():
                    raise ValueError(f"TeX input is missing: {raw}")
                return expand(strip_comments(path.read_text(encoding="utf-8")), (*active, path), preamble=preamble)
            slot = slots.get(match.group(2), {})
            if not expand_prose:
                return match.group(0)
            if planned:
                return " ".join(rf"\ref{{{label}}}" for label in slot.get("planned_references", []))
            path = experiment / str(slot.get("typeset_file", ""))
            return strip_comments(path.read_text(encoding="utf-8")) if path.is_file() else " ".join(rf"\ref{{{label}}}" for label in slot.get("planned_references", []))
        return re.sub(pattern, replace, text)

    text = strip_comments(main.read_text(encoding="utf-8"))
    if r"\begin{document}" not in text:
        raise ValueError("main.tex has no document body")
    preamble, body = text.split(r"\begin{document}", 1)
    return expand(preamble, (main.resolve(),), preamble=True) + r"\begin{document}" + "\n" + expand(body, (main.resolve(),))
