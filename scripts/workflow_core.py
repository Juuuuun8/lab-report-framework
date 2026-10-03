#!/usr/bin/env python3
"""Shared primitives for the three-gate, human-approved workflow."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

import yaml


GATES = ("G1", "G2", "G3")
GATE_TITLES = {
    "G1": "実験前確認",
    "G2": "証拠・骨格確認",
    "G3": "完成稿・提出確認",
}

GATE_PATHS = {
    "G1": (
        "instructions",
        "QUESTIONS.md",
        "spec/USER_DECISIONS.yaml",
        "spec/REPORT_META.yaml",
        "spec/ASSIGNMENT_REQUIREMENTS.yaml",
        "spec/ACADEMIC_INTEGRITY.yaml",
        "spec/EXPERIMENT_PLAN.yaml",
        "spec/CONTEXT_INDEX.yaml",
        "spec/STYLE_OVERRIDES.yaml",
    ),
    "G2": (
        "spec/EXECUTION_MANIFEST.yaml",
        "spec/REPRODUCE.yaml",
        "spec/SOURCES.yaml",
        "spec/CLAIMS.yaml",
        "data/raw",
        "data/processed",
        "analysis",
        "RESULT_TRACEABILITY.md",
        "SOURCE_AUDIT.md",
        "spec/WRITING_PLAN.yaml",
        "report",
        "quality/SKELETON_BUILD.yaml",
    ),
    "G3": (
        "report",
        "prose",
        "spec/WRITING_PLAN.yaml",
        "HANDOFF.md",
        "PROFESSOR_EVALUATION.md",
        "RUBRIC_TRACEABILITY.md",
        "ORAL_DEFENSE.md",
        "WORKLOG.md",
        "quality/FINAL_CHECK.yaml",
        "quality/QUALITY_REVIEW.yaml",
        "quality/PROFESSOR_REVIEW.yaml",
        "quality/RENDER_MANIFEST.yaml",
        "quality/CANDIDATE_BUILD.yaml",
        "quality/PROSE_DIFF.md",
        "SOURCE_AUDIT.md",
        "RESULT_TRACEABILITY.md",
        "spec/ACADEMIC_INTEGRITY.yaml",
        "build/final-candidate.pdf",
    ),
}

TEXT_SUFFIXES = {".md", ".tex", ".yaml", ".yml", ".json", ".csv", ".txt", ".dat", ".py"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def state_path(experiment: Path) -> Path:
    return experiment / "workflow" / "STATE.yaml"


def review_path(experiment: Path, gate: str) -> Path:
    return experiment / "workflow" / f"{gate}_REVIEW.md"


def load_state(experiment: Path) -> dict:
    path = state_path(experiment)
    if not path.is_file():
        raise FileNotFoundError(f"workflow state is missing: {path}; run workflow.py init")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid workflow state: {path}")
    return data


def write_state(experiment: Path, state: dict) -> None:
    path = state_path(experiment)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".state-", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(yaml.safe_dump(state, allow_unicode=True, sort_keys=False))
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def normalized_payload(path: Path) -> bytes:
    """Return stable bytes for auditable content across Windows and Unix."""
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return path.read_bytes()


def content_fingerprint(path: Path) -> tuple[str, int]:
    payload = normalized_payload(path)
    return hashlib.sha256(payload).hexdigest(), len(payload)


def gate_fingerprint(experiment: Path, gate: str, path: Path) -> tuple[str, int]:
    """Hash only the G2-approved structural part of the writing plan.

    Prose receipt status, original hashes, and proofreading notes are expected to
    change after G2. G3 hashes the complete file through content_fingerprint.
    """
    if gate == "G1" and path == experiment / "spec/ACADEMIC_INTEGRITY.yaml":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.pop("confirmations", None)
        payload = yaml.safe_dump(data, allow_unicode=True, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest(), len(payload)
    if gate == "G2" and path == experiment / "spec" / "WRITING_PLAN.yaml":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        stable = {
            "version": data.get("version"),
            "skeleton_pdf": data.get("skeleton_pdf"),
            "slots": [
                {
                    key: slot.get(key)
                    for key in (
                        "slot_id",
                        "display_label",
                        "section",
                        "purpose",
                        "required_points",
                        "planned_references",
                        "evidence_ids",
                        "rubric_ids",
                        "authorship",
                    )
                }
                for slot in data.get("slots", [])
            ],
        }
        payload = yaml.safe_dump(stable, allow_unicode=True, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest(), len(payload)
    return content_fingerprint(path)


def gate_files(experiment: Path, gate: str) -> list[Path]:
    files: list[Path] = []
    for relative in GATE_PATHS[gate]:
        candidate = experiment / relative
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                item for item in candidate.rglob("*")
                if item.is_file()
                and item.name != ".gitkeep"
                and "rendered" not in item.parts
                and not (set(item.parts) & IGNORED_PARTS)
                and item.suffix.lower() not in IGNORED_SUFFIXES
            )
    return sorted(set(files), key=lambda item: item.relative_to(experiment).as_posix())


def gate_manifest(experiment: Path, gate: str) -> list[dict[str, object]]:
    manifest = []
    for path in gate_files(experiment, gate):
        digest, size = gate_fingerprint(experiment, gate, path)
        manifest.append({
            "path": path.relative_to(experiment).as_posix(),
            "sha256": digest,
            "bytes": size,
        })
    # Approval of evidence/structure is conditional on the exact upstream plan.
    for prior in GATES[:GATES.index(gate)]:
        digest, _ = gate_digest(experiment, prior)
        manifest.append({"path": f"@approval/{prior}", "sha256": digest, "bytes": 0})
    if gate == "G2":
        data = yaml.safe_load((experiment / "spec/ACADEMIC_INTEGRITY.yaml").read_text(encoding="utf-8")) or {}
        subset = {key: data.get("confirmations", {}).get(key) for key in ("actual_work_status", "data_not_fabricated")}
        payload = yaml.safe_dump(subset, sort_keys=True).encode("utf-8")
        manifest.append({"path": "@execution-confirmations", "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)})
    # build/ is intentionally ignored by Git. After release, a clean clone can
    # therefore use the byte-identical released PDF as the logical candidate
    # artifact when verifying the recorded G3 approval.
    if gate == "G3" and not any(item["path"] == "build/final-candidate.pdf" for item in manifest):
        released = experiment / "deliverables" / "report.pdf"
        if released.is_file():
            digest, size = content_fingerprint(released)
            manifest.append({
                "path": "build/final-candidate.pdf",
                "sha256": digest,
                "bytes": size,
            })
            manifest.sort(key=lambda item: str(item["path"]))
    return manifest


def manifest_digest(manifest: list[dict[str, object]]) -> str:
    # File size is useful review metadata, but it is excluded from the approval
    # digest because line-ending conversion can change text byte counts without
    # changing normalized content.
    lines = [f"{item['path']}\0{item['sha256']}" for item in manifest]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def gate_digest(experiment: Path, gate: str) -> tuple[str, list[dict[str, object]]]:
    manifest = gate_manifest(experiment, gate)
    return manifest_digest(manifest), manifest


def approval_current(experiment: Path, gate: str) -> tuple[bool, str]:
    try:
        state = load_state(experiment)
    except (FileNotFoundError, ValueError) as exc:
        return False, str(exc)
    approval = state.get("gates", {}).get(gate, {})
    if approval.get("status") != "approved":
        return False, f"{gate} has not been approved by the user"
    decided_by = approval.get("decided_by")
    if decided_by != "user":
        if decided_by != "framework_migration" or state.get("example_only") is not True:
            return False, f"{gate} approval is not a user approval"
        try:
            experiment.resolve().relative_to((Path(__file__).resolve().parents[1] / "examples").resolve())
        except ValueError:
            return False, f"{gate} migration approval is valid only under examples/"
    current, _ = gate_digest(experiment, gate)
    if current != approval.get("artifact_digest"):
        return False, f"{gate} approval is stale because reviewed artifacts changed"
    if gate in {"G2", "G3"}:
        from artifact_checks import verify_build
        mode = "skeleton" if gate == "G2" else "candidate"
        pdf = experiment / "build" / ("skeleton.pdf" if gate == "G2" else "final-candidate.pdf")
        if gate == "G2" and not pdf.is_file():
            pdf = experiment / "preview/skeleton.pdf"
        if gate == "G3" and not pdf.is_file():
            pdf = experiment / "deliverables/report.pdf"
        try:
            verify_build(experiment, mode, pdf if pdf.is_file() else None)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            return False, f"{gate}: {exc}"
    return True, "approved and current"


def require_prior_approvals(experiment: Path, gate: str) -> list[str]:
    errors: list[str] = []
    for prior in GATES[: GATES.index(gate)]:
        ok, reason = approval_current(experiment, prior)
        if not ok:
            errors.append(reason)
    return errors
