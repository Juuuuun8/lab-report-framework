#!/usr/bin/env python3
"""Validate the cumulative PHASE 0-8 gates for one experiment."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from workflow_core import approval_current, content_fingerprint


PLACEHOLDER = re.compile(r"\bTODO\b|指定待ち|未確認|未実施|\{\{.+?\}\}")
SCHEMAS = {
    "REPORT_META.yaml": "report-meta.schema.json",
    "USER_DECISIONS.yaml": "user-decisions.schema.json",
    "EXPERIMENT_PLAN.yaml": "experiment-plan.schema.json",
    "SOURCES.yaml": "sources.schema.json",
    "ASSIGNMENT_REQUIREMENTS.yaml": "assignment-requirements.schema.json",
    "ACADEMIC_INTEGRITY.yaml": "academic-integrity.schema.json",
    "CLAIMS.yaml": "claims.schema.json",
    "EXECUTION_MANIFEST.yaml": "execution-manifest.schema.json",
    "STYLE_OVERRIDES.yaml": "style-overrides.schema.json",
    "QUALITY_REVIEW.yaml": "quality-review.schema.json",
    "CONTEXT_INDEX.yaml": "context-index.schema.json",
    "REPRODUCE.yaml": "reproduce.schema.json",
    "IMPROVEMENT_BACKLOG.yaml": "improvement-backlog.schema.json",
    "STATE.yaml": "workflow-state.schema.json",
    "RENDER_MANIFEST.yaml": "render-manifest.schema.json",
}
FORBIDDEN_STYLE_COMMANDS = (
    r"\geometry",
    r"\newgeometry",
    r"\restoregeometry",
    r"\captionsetup",
    r"\pagestyle",
    r"\fancyhead",
    r"\fancyfoot",
    r"\setmainjfont",
    r"\setsansjfont",
    r"\fontsize",
    r"\linespread",
    r"\setstretch",
    r"\twocolumn",
    r"\onecolumn",
)


class Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def file(self, path: Path, message: str | None = None) -> None:
        self.require(path.is_file() and path.stat().st_size > 0, message or f"missing or empty: {path}")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path, audit: Audit) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001 - report malformed user inputs
        audit.errors.append(f"cannot read YAML {path}: {exc}")
        return {}


def load_structured(experiment: Path, relative: str, audit: Audit) -> dict:
    path = experiment / relative
    audit.file(path)
    if not path.is_file():
        return {}
    data = load_yaml(path, audit)
    schema_name = SCHEMAS.get(path.name)
    if schema_name and data:
        schema_path = repo_root() / "schemas" / schema_name
        audit.file(schema_path, f"schema is missing: {schema_path}")
        if schema_path.is_file():
            schema = load_yaml(schema_path, audit)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
                location = ".".join(str(part) for part in error.path) or "<root>"
                audit.errors.append(f"schema {path.name} {location}: {error.message}")
    return data


def unique_ids(items: list[dict], key: str, audit: Audit, phase: int) -> set[str]:
    values = [item.get(key) for item in items if item.get(key)]
    audit.require(len(values) == len(set(values)), f"PHASE {phase}: duplicate {key}")
    return set(values)


def meaningful_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [item for item in path.rglob("*") if item.is_file() and item.name != ".gitkeep" and item.stat().st_size > 0]


def text_without_placeholders(path: Path, audit: Audit, phase: int) -> str:
    audit.file(path)
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    audit.require(not PLACEHOLDER.search(text), f"PHASE {phase}: unresolved placeholder in {path}")
    return text


def check_instruction_source(experiment: Path, source: dict, audit: Audit) -> None:
    raw_path = str(source.get("path", ""))
    candidate = (experiment / raw_path).resolve()
    try:
        candidate.relative_to(experiment.resolve())
    except ValueError:
        audit.errors.append(f"PHASE 1: instruction path escapes experiment: {raw_path}")
        return
    audit.file(candidate, f"PHASE 1: instruction source missing: {raw_path}")
    expected_hash = source.get("sha256")
    if expected_hash and candidate.is_file():
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        audit.require(actual.lower() == str(expected_hash).lower(), f"PHASE 1: instruction hash mismatch: {raw_path}")


def check_tex(experiment: Path, audit: Audit, allowed_style_settings: set[str]) -> None:
    report = experiment / "report"
    tex_files = sorted(report.rglob("*.tex"))
    audit.require(bool(tex_files), "PHASE 6: report has no TeX files")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in tex_files)

    audit.require(r"\documentclass{labreport}" in combined, "PHASE 6: main document must use labreport class")
    for forbidden in [r"\twocolumn", r"\begin{abstract}", r"\maketitle", r"\author{"]:
        audit.require(forbidden not in combined, f"PHASE 6: forbidden report construct: {forbidden}")
    audit.require("[H]" not in combined, "PHASE 6: [H] float placement is prohibited without a recorded override")

    for command in FORBIDDEN_STYLE_COMMANDS:
        if command in combined:
            audit.require(command in allowed_style_settings, f"PHASE 6: style command requires approved STYLE_OVERRIDES entry: {command}")

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

    class_file = repo_root() / "tex" / "labreport.cls"
    if class_file.is_file():
        class_text = class_file.read_text(encoding="utf-8")
        audit.require("captionpos=t" in class_text, "PHASE 6: listing captions must be positioned above code")


def check_style_contract(audit: Audit) -> None:
    root = repo_root()
    contract_path = root / "config" / "style-contract.yaml"
    schema_path = root / "schemas" / "style-contract.schema.json"
    audit.file(contract_path, "PHASE 6: style contract is missing")
    audit.file(schema_path, "PHASE 6: style contract schema is missing")
    if not contract_path.is_file() or not schema_path.is_file():
        return
    contract = load_yaml(contract_path, audit)
    schema = load_yaml(schema_path, audit)
    for error in Draft202012Validator(schema).iter_errors(contract):
        location = ".".join(str(part) for part in error.path) or "<root>"
        audit.errors.append(f"schema style-contract.yaml {location}: {error.message}")
    class_path = root / str(contract.get("class_path", ""))
    audit.file(class_path, "PHASE 6: contracted TeX class is missing")
    if class_path.is_file():
        normalized = class_path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
        actual = hashlib.sha256(normalized).hexdigest()
        audit.require(
            actual == contract.get("normalized_sha256"),
            "PHASE 6: shared style changed without revising config/style-contract.yaml and completing visual review",
        )


def font_embedded(font: object) -> bool:
    try:
        value = font.get_object()
        if str(value.get("/Subtype")) == "/Type0":
            descendants = value.get("/DescendantFonts", [])
            return bool(descendants) and font_embedded(descendants[0])
        descriptor = value.get("/FontDescriptor")
        if descriptor is None:
            return str(value.get("/Subtype")) == "/Type3"
        descriptor = descriptor.get_object()
        return any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))
    except Exception:  # noqa: BLE001 - malformed PDFs are reported as non-embedded
        return False


def check_pdf_a4(pdf: Path, audit: Audit) -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        audit.errors.append("PHASE 8: pypdf is required; install requirements.txt")
        return 0
    try:
        reader = PdfReader(str(pdf))
        page_count = len(reader.pages)
        audit.require(page_count >= 2, "PHASE 8: report.pdf must contain a cover and body")
        for index, page in enumerate(reader.pages, 1):
            width = float(page.mediabox.width) * 25.4 / 72
            height = float(page.mediabox.height) * 25.4 / 72
            audit.require(abs(width - 210) < 1 and abs(height - 297) < 1, f"PHASE 8: page {index} is not A4 ({width:.1f} x {height:.1f} mm)")
            audit.require(bool((page.extract_text() or "").strip()), f"PHASE 8: page {index} has no extractable text")
            resources = page.get("/Resources", {})
            fonts = resources.get("/Font", {}) if resources else {}
            for font_name, font in fonts.items():
                audit.require(font_embedded(font), f"PHASE 8: page {index} font is not embedded: {font_name}")
            for annotation_ref in page.get("/Annots", []):
                annotation = annotation_ref.get_object()
                action = annotation.get("/A")
                if action and str(action.get("/S")) == "/URI":
                    audit.require(bool(str(action.get("/URI", "")).strip()), f"PHASE 8: page {index} has an empty URI link")
        return page_count
    except Exception as exc:  # noqa: BLE001
        audit.errors.append(f"PHASE 8: cannot inspect PDF: {exc}")
        return 0


def validate(experiment: Path, phase: int, candidate: bool = False) -> Audit:
    audit = Audit()

    inventory = experiment / "instructions" / "INPUT_INVENTORY.md"
    if phase >= 0:
        text_without_placeholders(inventory, audit, 0)

    requirements: dict = {}
    integrity: dict = {}
    decisions: dict = {}
    meta: dict = {}
    if phase >= 1:
        text_without_placeholders(experiment / "QUESTIONS.md", audit, 1)
        decisions = load_structured(experiment, "spec/USER_DECISIONS.yaml", audit)
        meta = load_structured(experiment, "spec/REPORT_META.yaml", audit)
        requirements = load_structured(experiment, "spec/ASSIGNMENT_REQUIREMENTS.yaml", audit)
        integrity = load_structured(experiment, "spec/ACADEMIC_INTEGRITY.yaml", audit)
        context_index = load_structured(experiment, "spec/CONTEXT_INDEX.yaml", audit)
        load_structured(experiment, "workflow/STATE.yaml", audit)

        audit.require(decisions.get("instructions_read_complete") is True, "PHASE 1: instructions_read_complete must be true")
        audit.require(bool(decisions.get("instructions_read_at")), "PHASE 1: instructions_read_at is required")
        questions = decisions.get("questions", [])
        audit.require(bool(questions), "PHASE 1: at least one documented question or confirmation is required")
        for question in questions:
            if question.get("required_before_experiment"):
                audit.require(question.get("status") in {"resolved", "delegated"}, f"PHASE 1: unresolved required question {question.get('id')}")
                audit.require(bool(question.get("decision")), f"PHASE 1: question {question.get('id')} has no decision")

        cover = meta.get("cover", {})
        audit.require(bool(cover.get("course_name")) and bool(cover.get("title")), "PHASE 1: cover course_name and title are required")
        audit.require(bool(cover.get("fields")), "PHASE 1: at least one user-specified cover field is required")
        audit.require(not PLACEHOLDER.search(str(cover)), "PHASE 1: cover metadata contains placeholders")
        doc = meta.get("document", {})
        audit.require(doc.get("paper") == "A4" and doc.get("columns") == 1 and doc.get("body_font_pt") == 10.5, "PHASE 1: document defaults must be A4, one column, 10.5pt unless an approved override exists")

        sources = requirements.get("instruction_sources", [])
        audit.require(bool(sources), "PHASE 1: instruction_sources must not be empty")
        unique_ids(sources, "instruction_id", audit, 1)
        for source in sources:
            audit.require(source.get("read_complete") is True, f"PHASE 1: instruction not fully read: {source.get('instruction_id')}")
            check_instruction_source(experiment, source, audit)
        reqs = requirements.get("requirements", [])
        rubrics = requirements.get("rubric_criteria", [])
        audit.require(bool(reqs), "PHASE 1: extracted requirements must not be empty")
        audit.require(bool(rubrics), "PHASE 1: rubric criteria must not be empty")
        unique_ids(reqs, "requirement_id", audit, 1)
        unique_ids(rubrics, "rubric_id", audit, 1)
        audit.require(not PLACEHOLDER.search(str(requirements)), "PHASE 1: assignment requirements contain placeholders")

        ai_use = integrity.get("ai_use", {})
        audit.require(ai_use.get("status") not in {None, "unknown"}, "PHASE 1: AI-use policy must be resolved before work starts")
        audit.require(ai_use.get("user_confirmed") is True, "PHASE 1: user must confirm the AI-use policy")
        for document in context_index.get("documents", []):
            relative = document.get("path", "")
            target = (experiment / relative).resolve()
            try:
                target.relative_to(experiment.resolve())
            except ValueError:
                audit.errors.append(f"PHASE 1: context path escapes experiment: {relative}")
                continue
            audit.file(target, f"PHASE 1: indexed context is missing: {relative}")
            if target.is_file() and document.get("sha256"):
                actual = hashlib.sha256(target.read_bytes()).hexdigest()
                audit.require(actual == document.get("sha256"), f"PHASE 1: indexed context changed and must be reread: {relative}")
            audit.require(not PLACEHOLDER.search(str(document.get("verified_summary", ""))), f"PHASE 1: context summary is unresolved: {relative}")

    if phase >= 2:
        plan = load_structured(experiment, "spec/EXPERIMENT_PLAN.yaml", audit)
        audit.require(plan.get("status") == "approved", "PHASE 2: experiment plan must be approved")
        audit.require(plan.get("safety_reviewed") is True, "PHASE 2: safety_reviewed must be true")
        for key in ["objective", "independent_variables", "dependent_variables", "replications", "execution_order", "exclusion_rules", "stop_conditions", "analysis"]:
            audit.require(bool(plan.get(key)), f"PHASE 2: plan field is missing: {key}")
        audit.require(not PLACEHOLDER.search(str(plan)), "PHASE 2: experiment plan contains placeholders")

    if phase >= 3:
        approved, reason = approval_current(experiment, "G1")
        audit.require(approved, f"PHASE 3: {reason}")
        audit.require(bool(meaningful_files(experiment / "data" / "raw")), "PHASE 3: raw data is required")
        manifest = load_structured(experiment, "spec/EXECUTION_MANIFEST.yaml", audit)
        audit.require(not PLACEHOLDER.search(str(manifest)), "PHASE 3: execution manifest contains placeholders")
        runs = manifest.get("runs", [])
        unique_ids(runs, "run_id", audit, 3)
        for run in runs:
            for raw_file in run.get("raw_files", []):
                raw_relative = raw_file.get("path", "") if isinstance(raw_file, dict) else str(raw_file)
                raw_path = (experiment / raw_relative).resolve()
                try:
                    raw_path.relative_to(experiment.resolve())
                    audit.file(raw_path, f"PHASE 3: run {run.get('run_id')} raw file missing: {raw_relative}")
                    if raw_path.is_file() and isinstance(raw_file, dict):
                        actual_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
                        audit.require(actual_hash == raw_file.get("sha256"), f"PHASE 3: raw data hash mismatch: {raw_relative}")
                        audit.require(raw_path.stat().st_size == raw_file.get("bytes"), f"PHASE 3: raw data size mismatch: {raw_relative}")
                except ValueError:
                    audit.errors.append(f"PHASE 3: raw file path escapes experiment: {raw_relative}")
        audit.require(bool(manifest.get("sealed_at")), "PHASE 3: raw data manifest has not been sealed")
        worklog = experiment / "WORKLOG.md"
        audit.file(worklog)
        if worklog.is_file():
            audit.require("PHASE 3" in worklog.read_text(encoding="utf-8"), "PHASE 3: WORKLOG has no execution record")
        confirmations = integrity.get("confirmations", {}) if integrity else load_structured(experiment, "spec/ACADEMIC_INTEGRITY.yaml", audit).get("confirmations", {})
        audit.require(confirmations.get("actual_work_status") in {"confirmed", "not_applicable"}, "PHASE 3: actual work status is not confirmed")
        audit.require(confirmations.get("data_not_fabricated") is True, "PHASE 3: data integrity is not confirmed")

    result_ids: set[str] = set()
    if phase >= 4:
        audit.require(bool(meaningful_files(experiment / "data" / "processed")), "PHASE 4: processed data is required")
        audit.require(bool(meaningful_files(experiment / "analysis")), "PHASE 4: analysis code is required")
        trace_text = text_without_placeholders(experiment / "RESULT_TRACEABILITY.md", audit, 4)
        result_ids = set(re.findall(r"\bR-[0-9]{3}\b", trace_text))
        audit.require(bool(result_ids), "PHASE 4: result traceability must contain completed R- IDs")
        reproduce = load_structured(experiment, "spec/REPRODUCE.yaml", audit)
        audit.require(bool(reproduce.get("sealed_at")), "PHASE 4: analysis outputs have not been sealed")
        for output in reproduce.get("expected_outputs", []):
            relative = output.get("path", "")
            target = (experiment / relative).resolve()
            try:
                target.relative_to(experiment.resolve())
                audit.file(target, f"PHASE 4: expected analysis output missing: {relative}")
                if target.is_file():
                    actual_hash, actual_size = content_fingerprint(target)
                    audit.require(actual_hash == output.get("sha256"), f"PHASE 4: analysis output hash mismatch: {relative}")
                    audit.require(actual_size == output.get("bytes"), f"PHASE 4: analysis output size mismatch: {relative}")
            except ValueError:
                audit.errors.append(f"PHASE 4: analysis output path escapes experiment: {relative}")

    claims: list[dict] = []
    source_ids: set[str] = set()
    if phase >= 5:
        sources_data = load_structured(experiment, "spec/SOURCES.yaml", audit)
        claims_data = load_structured(experiment, "spec/CLAIMS.yaml", audit)
        sources = sources_data.get("sources", [])
        claims = claims_data.get("claims", [])
        source_ids = unique_ids(sources, "source_id", audit, 5)
        claim_ids = unique_ids(claims, "claim_id", audit, 5)
        audit.require(bool(claims), "PHASE 5: claim inventory must not be empty")
        for source in sources:
            verification = source.get("verification", {})
            audit.require(verification.get("status") == "verified", f"PHASE 5: source {source.get('source_id')} is not verified")
            for key in ["locator", "supports_claims", "match_note", "selection_note"]:
                audit.require(bool(verification.get(key)), f"PHASE 5: source {source.get('source_id')} lacks {key}")
            unknown_claims = set(verification.get("supports_claims", [])) - claim_ids
            audit.require(not unknown_claims, f"PHASE 5: source {source.get('source_id')} references unknown claims: {sorted(unknown_claims)}")
        for claim in claims:
            claim_id = claim.get("claim_id")
            audit.require(claim.get("status") == "verified", f"PHASE 5: claim {claim_id} is not verified")
            audit.require(not PLACEHOLDER.search(str(claim)), f"PHASE 5: claim {claim_id} contains placeholders")
            linked_sources = set(claim.get("source_ids", []))
            linked_results = set(claim.get("result_ids", []))
            audit.require(not (linked_sources - source_ids), f"PHASE 5: claim {claim_id} has unknown source IDs")
            if claim.get("kind") == "external":
                audit.require(bool(linked_sources), f"PHASE 5: external claim {claim_id} has no source")
            if claim.get("kind") == "result":
                audit.require(bool(linked_results), f"PHASE 5: result claim {claim_id} has no result ID")
            if claim.get("kind") == "inference":
                audit.require(bool(linked_sources or linked_results), f"PHASE 5: inference claim {claim_id} has no evidence")
            if result_ids:
                audit.require(not (linked_results - result_ids), f"PHASE 5: claim {claim_id} references unknown result IDs")
        source_audit = text_without_placeholders(experiment / "SOURCE_AUDIT.md", audit, 5)
        for source_id in source_ids:
            audit.require(source_id in source_audit, f"PHASE 5: SOURCE_AUDIT lacks {source_id}")
        for claim in claims:
            if claim.get("source_ids"):
                audit.require(claim.get("claim_id") in source_audit, f"PHASE 5: SOURCE_AUDIT lacks {claim.get('claim_id')}")

    if phase >= 6:
        approved, reason = approval_current(experiment, "G2")
        audit.require(approved, f"PHASE 6: {reason}")
        check_style_contract(audit)
        overrides = load_structured(experiment, "spec/STYLE_OVERRIDES.yaml", audit)
        allowed = {str(item.get("setting")) for item in overrides.get("overrides", [])}
        check_tex(experiment, audit, allowed)
        text_without_placeholders(experiment / "HANDOFF.md", audit, 6)
        requirements = requirements or load_structured(experiment, "spec/ASSIGNMENT_REQUIREMENTS.yaml", audit)
        rubric_path = experiment / "RUBRIC_TRACEABILITY.md"
        if rubric_path.is_file():
            rubric_text = text_without_placeholders(rubric_path, audit, 6)
            for criterion in requirements.get("rubric_criteria", []):
                audit.require(criterion.get("rubric_id") in rubric_text, f"PHASE 6: RUBRIC_TRACEABILITY lacks {criterion.get('rubric_id')}")
        for claim in claims or load_structured(experiment, "spec/CLAIMS.yaml", audit).get("claims", []):
            audit.require(bool(claim.get("report_locator")), f"PHASE 6: claim {claim.get('claim_id')} has no report locator")

    if phase >= 7:
        worklog = experiment / "WORKLOG.md"
        text = worklog.read_text(encoding="utf-8") if worklog.is_file() else ""
        audit.require("Codex再監査: 完了" in text, "PHASE 7: Codex re-audit is not recorded as complete")
        antigravity_not_used = any(marker in text for marker in (
            "Antigravity利用: なし",
            "Antigravity変更受領: 完成例はCodex初稿のため変更なし",
            "Antigravity変更受領: なし",
        ))
        baseline = experiment / "quality" / "POLISH_BASELINE.json"
        audit.require(antigravity_not_used or baseline.is_file(), "PHASE 7: polish baseline is required when Antigravity edited the report")
        if baseline.is_file():
            from polish_guard import baseline_path, protected_snapshot

            expected = yaml.safe_load(baseline_path(experiment).read_text(encoding="utf-8"))
            audit.require(expected == protected_snapshot(experiment / "report"), "PHASE 7: protected technical content changed during polishing")

    if phase >= 8:
        required_files = [
            "HANDOFF.md",
            "SOURCE_AUDIT.md",
            "RESULT_TRACEABILITY.md",
            "WORKLOG.md",
        ]
        if candidate:
            for name in required_files:
                audit.file(experiment / name, f"PHASE 8: missing candidate artifact {name}")
            audit.file(experiment / "quality" / "QUALITY_REVIEW.yaml", "PHASE 8: missing internal quality review")
        else:
            base = experiment / "deliverables"
            for name in [*required_files, "report.pdf"]:
                audit.file(base / name, f"PHASE 8: missing deliverable {name}")
            approved, reason = approval_current(experiment, "G3")
            audit.require(approved, f"PHASE 8: {reason}")

        final_check = load_yaml(experiment / "quality" / "FINAL_CHECK.yaml", audit)
        audit.require(final_check.get("visual_review", {}).get("status") == "passed", "PHASE 8: visual review must be passed")
        audit.require(final_check.get("technical_review", {}).get("status") == "passed", "PHASE 8: technical review must be passed")

        quality = load_structured(experiment, "quality/QUALITY_REVIEW.yaml", audit)
        rubric_reviews = quality.get("rubric", [])
        reviewed_ids = unique_ids(rubric_reviews, "rubric_id", audit, 8)
        requirements = requirements or load_structured(experiment, "spec/ASSIGNMENT_REQUIREMENTS.yaml", audit)
        required_rubrics = {item.get("rubric_id") for item in requirements.get("rubric_criteria", []) if item.get("required")}
        audit.require(required_rubrics <= reviewed_ids, f"PHASE 8: missing rubric reviews: {sorted(required_rubrics - reviewed_ids)}")
        for item in rubric_reviews:
            audit.require(item.get("status") in {"passed", "not_applicable"}, f"PHASE 8: rubric {item.get('rubric_id')} did not pass")
            audit.require(bool(item.get("report_locators")), f"PHASE 8: rubric {item.get('rubric_id')} has no report locator")
            audit.require(bool(item.get("evidence")), f"PHASE 8: rubric {item.get('rubric_id')} has no evidence")
        for name, check in quality.get("content_checks", {}).items():
            audit.require(check.get("status") == "passed", f"PHASE 8: content check failed: {name}")
        quality_text = str(quality)
        required_requirements = {
            item.get("requirement_id") for item in requirements.get("requirements", []) if item.get("mandatory")
        }
        for requirement_id in required_requirements:
            audit.require(requirement_id in quality_text, f"PHASE 8: QUALITY_REVIEW lacks mandatory {requirement_id}")

        oral_path = experiment / "ORAL_DEFENSE.md"
        if oral_path.is_file():
            oral = text_without_placeholders(oral_path, audit, 8)
            audit.require(bool(re.search(r"\bO-[0-9]{3}\b", oral)), "PHASE 8: ORAL_DEFENSE has no completed questions")
        integrity = integrity or load_structured(experiment, "spec/ACADEMIC_INTEGRITY.yaml", audit)
        confirmations = integrity.get("confirmations", {})
        audit.require(confirmations.get("sources_not_fabricated") is True, "PHASE 8: source integrity is not confirmed")
        audit.require(confirmations.get("student_can_explain") is True, "PHASE 8: student understanding is not confirmed")

        if (experiment / "IMPROVEMENT_BACKLOG.yaml").is_file():
            load_structured(experiment, "IMPROVEMENT_BACKLOG.yaml", audit)
        pdf = experiment / "build" / "final-candidate.pdf" if candidate else experiment / "deliverables" / "report.pdf"
        page_count = check_pdf_a4(pdf, audit) if pdf.is_file() else 0
        rendered_pages = final_check.get("visual_review", {}).get("rendered_pages")
        audit.require(rendered_pages == page_count, f"PHASE 8: rendered page count {rendered_pages} does not match PDF page count {page_count}")
        render_manifest = load_structured(experiment, "quality/RENDER_MANIFEST.yaml", audit)
        if pdf.is_file():
            audit.require(
                render_manifest.get("source_sha256") == hashlib.sha256(pdf.read_bytes()).hexdigest(),
                "PHASE 8: visual review manifest does not match the PDF being validated",
            )
        audit.require(render_manifest.get("page_count") == page_count, "PHASE 8: render manifest page count does not match PDF")
        audit.require(len(render_manifest.get("pages", [])) == page_count, "PHASE 8: render manifest page list is incomplete")
        if candidate:
            manifest_root = experiment / "quality"
            for page in render_manifest.get("pages", []):
                relative = page.get("path", "")
                rendered = (manifest_root / relative).resolve()
                try:
                    rendered.relative_to(manifest_root.resolve())
                    audit.file(rendered, f"PHASE 8: rendered review page is missing: {relative}")
                    if rendered.is_file():
                        audit.require(hashlib.sha256(rendered.read_bytes()).hexdigest() == page.get("sha256"), f"PHASE 8: rendered page hash mismatch: {relative}")
                        audit.require(rendered.stat().st_size == page.get("bytes"), f"PHASE 8: rendered page size mismatch: {relative}")
                except ValueError:
                    audit.errors.append(f"PHASE 8: rendered page path escapes quality directory: {relative}")

    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--phase", type=int, choices=range(0, 9), required=True)
    parser.add_argument("--candidate", action="store_true", help="validate build/final-candidate.pdf before user release approval")
    args = parser.parse_args()
    experiment = args.experiment.resolve()
    if not experiment.is_dir():
        parser.error(f"not a directory: {experiment}")

    audit = validate(experiment, args.phase, candidate=args.candidate)
    label = "最終候補検査" if args.candidate and args.phase == 8 else f"PHASE 0-{args.phase}"
    if audit.errors:
        print(f"FAIL: {label}")
        for error in audit.errors:
            print(f"- {error}")
        return 1
    if args.candidate and args.phase == 8:
        print("PASS: 最終候補検査（提出版の確定にはG3承認が必要）")
    else:
        print(f"PASS: {label}")
    for note in audit.notes:
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
