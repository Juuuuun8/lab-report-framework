#!/usr/bin/env python3
"""Validate the cumulative PHASE 0-8 gates for one experiment."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


PLACEHOLDER = re.compile(r"\bTODO\b|指定待ち|未確認|未実施|\{\{.+?\}\}")


class Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def file(self, path: Path, message: str | None = None) -> None:
        self.require(path.is_file() and path.stat().st_size > 0, message or f"missing or empty: {path}")


def load_yaml(path: Path, audit: Audit) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001 - report all malformed user inputs
        audit.errors.append(f"cannot read YAML {path}: {exc}")
        return {}


def meaningful_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [item for item in path.rglob("*") if item.is_file() and item.name != ".gitkeep" and item.stat().st_size > 0]


def check_tex(experiment: Path, audit: Audit) -> None:
    report = experiment / "report"
    tex_files = sorted(report.rglob("*.tex"))
    audit.require(bool(tex_files), "PHASE 6: report has no TeX files")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in tex_files)

    audit.require(r"\documentclass{labreport}" in combined, "PHASE 6: main document must use labreport class")
    for forbidden in [r"\twocolumn", r"\begin{abstract}", r"\maketitle", r"\author{"]:
        audit.require(forbidden not in combined, f"PHASE 6: forbidden report construct: {forbidden}")
    audit.require("[H]" not in combined, "PHASE 6: [H] float placement is prohibited without a recorded override")

    for path in tex_files:
        text = path.read_text(encoding="utf-8")
        if path.name != "meta.tex":
            audit.require(not PLACEHOLDER.search(text), f"PHASE 6: unresolved placeholder in {path}")

    for env in ("figure", "table"):
        pattern = re.compile(rf"\\begin\{{{env}\}}.*?\\end\{{{env}\}}", re.S)
        for block in pattern.finditer(combined):
            body = block.group(0)
            caption = body.find(r"\caption")
            label_match = re.search(r"\\label\{([^}]+)\}", body)
            audit.require(caption >= 0, f"PHASE 6: {env} has no caption")
            audit.require(label_match is not None, f"PHASE 6: {env} has no label")
            if env == "figure":
                graphic = body.find(r"\includegraphics")
                audit.require(graphic < 0 or caption > graphic, "PHASE 6: figure caption must be below the figure")
            else:
                tabular_positions = [p for p in (body.find(r"\begin{tabular}"), body.find(r"\begin{tabularx}")) if p >= 0]
                if tabular_positions:
                    audit.require(caption < min(tabular_positions), "PHASE 6: table caption must be above the table")
            if label_match:
                label = label_match.group(1)
                first_reference = combined.find(rf"\ref{{{label}}}")
                audit.require(0 <= first_reference < block.start(), f"PHASE 6: {env} {label} must be referenced before placement")

    listing_pattern = re.compile(r"\\begin\{lstlisting\}(?:\[[^\]]*\])?.*?\\end\{lstlisting\}", re.S)
    for block in listing_pattern.finditer(combined):
        body = block.group(0)
        caption_match = re.search(r"caption=\{([^}]*)\}", body)
        label_match = re.search(r"label=\{([^}]+)\}", body)
        audit.require(caption_match is not None, "PHASE 6: lstlisting has no caption")
        audit.require(label_match is not None, "PHASE 6: lstlisting has no label")
        if label_match:
            label = label_match.group(1)
            first_reference = combined.find(rf"\ref{{{label}}}")
            audit.require(0 <= first_reference < block.start(), f"PHASE 6: listing {label} must be referenced before placement")

    class_file = Path(__file__).resolve().parents[1] / "tex" / "labreport.cls"
    if class_file.is_file():
        class_text = class_file.read_text(encoding="utf-8")
        audit.require("captionpos=t" in class_text, "PHASE 6: listing captions must be positioned above code")


def check_pdf_a4(pdf: Path, audit: Audit) -> None:
    try:
        from pypdf import PdfReader
    except ImportError:
        audit.errors.append("PHASE 8: pypdf is required; install requirements.txt")
        return
    try:
        reader = PdfReader(str(pdf))
        audit.require(len(reader.pages) >= 2, "PHASE 8: report.pdf must contain a cover and body")
        for index, page in enumerate(reader.pages, 1):
            width = float(page.mediabox.width) * 25.4 / 72
            height = float(page.mediabox.height) * 25.4 / 72
            audit.require(abs(width - 210) < 1 and abs(height - 297) < 1, f"PHASE 8: page {index} is not A4 ({width:.1f} x {height:.1f} mm)")
    except Exception as exc:  # noqa: BLE001
        audit.errors.append(f"PHASE 8: cannot inspect PDF: {exc}")


def validate(experiment: Path, phase: int) -> Audit:
    audit = Audit()

    inventory = experiment / "instructions" / "INPUT_INVENTORY.md"
    if phase >= 0:
        audit.file(inventory, "PHASE 0: INPUT_INVENTORY.md is required")
        if inventory.is_file():
            audit.require(not PLACEHOLDER.search(inventory.read_text(encoding="utf-8")), "PHASE 0: input inventory contains placeholders")

    if phase >= 1:
        audit.file(experiment / "QUESTIONS.md", "PHASE 1: QUESTIONS.md is required")
        decisions_path = experiment / "spec" / "USER_DECISIONS.yaml"
        meta_path = experiment / "spec" / "REPORT_META.yaml"
        audit.file(decisions_path)
        audit.file(meta_path)
        decisions = load_yaml(decisions_path, audit) if decisions_path.is_file() else {}
        audit.require(decisions.get("instructions_read_complete") is True, "PHASE 1: instructions_read_complete must be true")
        audit.require(bool(decisions.get("instructions_read_at")), "PHASE 1: instructions_read_at is required")
        for question in decisions.get("questions", []):
            if question.get("required_before_experiment"):
                audit.require(question.get("status") in {"resolved", "delegated"}, f"PHASE 1: unresolved required question {question.get('id')}")
                audit.require(bool(question.get("decision")), f"PHASE 1: question {question.get('id')} has no decision")
        meta = load_yaml(meta_path, audit) if meta_path.is_file() else {}
        cover = meta.get("cover", {})
        audit.require(bool(cover.get("course_name")) and bool(cover.get("title")), "PHASE 1: cover course_name and title are required")
        audit.require(bool(cover.get("fields")), "PHASE 1: at least one user-specified cover field is required")
        audit.require(not PLACEHOLDER.search(str(cover)), "PHASE 1: cover metadata contains placeholders")
        doc = meta.get("document", {})
        audit.require(doc.get("paper") == "A4" and doc.get("columns") == 1 and doc.get("body_font_pt") == 10.5, "PHASE 1: document defaults must be A4, one column, 10.5pt unless an override is recorded")

    if phase >= 2:
        plan_path = experiment / "spec" / "EXPERIMENT_PLAN.yaml"
        audit.file(plan_path)
        plan = load_yaml(plan_path, audit) if plan_path.is_file() else {}
        audit.require(plan.get("status") == "approved", "PHASE 2: experiment plan must be approved")
        audit.require(plan.get("safety_reviewed") is True, "PHASE 2: safety_reviewed must be true")
        for key in ["objective", "independent_variables", "dependent_variables", "replications", "execution_order", "exclusion_rules", "stop_conditions", "analysis"]:
            audit.require(bool(plan.get(key)), f"PHASE 2: plan field is missing: {key}")
        audit.require(not PLACEHOLDER.search(str(plan)), "PHASE 2: experiment plan contains placeholders")

    if phase >= 3:
        audit.require(bool(meaningful_files(experiment / "data" / "raw")), "PHASE 3: raw data is required")
        worklog = experiment / "WORKLOG.md"
        audit.file(worklog)
        if worklog.is_file():
            audit.require("PHASE 3" in worklog.read_text(encoding="utf-8"), "PHASE 3: WORKLOG has no execution record")

    if phase >= 4:
        audit.require(bool(meaningful_files(experiment / "data" / "processed")), "PHASE 4: processed data is required")
        audit.require(bool(meaningful_files(experiment / "analysis")), "PHASE 4: analysis code is required")
        trace = experiment / "RESULT_TRACEABILITY.md"
        audit.file(trace)
        if trace.is_file():
            trace_text = trace.read_text(encoding="utf-8")
            audit.require("R-" in trace_text and not PLACEHOLDER.search(trace_text), "PHASE 4: result traceability must contain completed R- IDs")

    if phase >= 5:
        sources_path = experiment / "spec" / "SOURCES.yaml"
        audit.file(sources_path)
        sources = load_yaml(sources_path, audit).get("sources", []) if sources_path.is_file() else []
        for source in sources:
            verification = source.get("verification", {})
            audit.require(verification.get("status") == "verified", f"PHASE 5: source {source.get('source_id')} is not verified")
            for key in ["locator", "supports_claims", "match_note", "selection_note"]:
                audit.require(bool(verification.get(key)), f"PHASE 5: source {source.get('source_id')} lacks {key}")
            for key in ["organization", "title", "url", "accessed_at", "language", "source_class"]:
                audit.require(bool(source.get(key)), f"PHASE 5: source {source.get('source_id')} lacks {key}")
        source_audit = experiment / "SOURCE_AUDIT.md"
        audit.file(source_audit)
        if source_audit.is_file():
            audit.require(not PLACEHOLDER.search(source_audit.read_text(encoding="utf-8")), "PHASE 5: SOURCE_AUDIT contains placeholders")

    if phase >= 6:
        check_tex(experiment, audit)
        handoff = experiment / "HANDOFF.md"
        audit.file(handoff)
        if handoff.is_file():
            audit.require(not PLACEHOLDER.search(handoff.read_text(encoding="utf-8")), "PHASE 6: HANDOFF contains placeholders")

    if phase >= 7:
        worklog = experiment / "WORKLOG.md"
        text = worklog.read_text(encoding="utf-8") if worklog.is_file() else ""
        audit.require("Codex再監査: 完了" in text, "PHASE 7: Codex re-audit is not recorded as complete")

    if phase >= 8:
        deliverables = experiment / "deliverables"
        required = ["report.pdf", "HANDOFF.md", "SOURCE_AUDIT.md", "RESULT_TRACEABILITY.md", "WORKLOG.md"]
        for name in required:
            audit.file(deliverables / name, f"PHASE 8: missing deliverable {name}")
        final_check = experiment / "quality" / "FINAL_CHECK.yaml"
        audit.file(final_check)
        checks = load_yaml(final_check, audit) if final_check.is_file() else {}
        audit.require(checks.get("visual_review", {}).get("status") == "passed", "PHASE 8: visual review must be passed")
        audit.require(checks.get("technical_review", {}).get("status") == "passed", "PHASE 8: technical review must be passed")
        pdf = deliverables / "report.pdf"
        if pdf.is_file():
            check_pdf_a4(pdf, audit)

    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--phase", type=int, choices=range(0, 9), required=True)
    args = parser.parse_args()
    experiment = args.experiment.resolve()
    if not experiment.is_dir():
        parser.error(f"not a directory: {experiment}")

    audit = validate(experiment, args.phase)
    if audit.errors:
        print(f"FAIL: PHASE 0-{args.phase}")
        for error in audit.errors:
            print(f"- {error}")
        return 1
    print(f"PASS: PHASE 0-{args.phase}")
    for note in audit.notes:
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
