#!/usr/bin/env python3
"""Shared primitives for the three-gate, human-approved workflow."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


GATES = ("G1", "G2", "G3")
GATE_TITLES = {
    "G1": "実験契約",
    "G2": "証拠と論証方針",
    "G3": "提出",
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
    ),
    "G3": (
        "report",
        "HANDOFF.md",
        "RUBRIC_TRACEABILITY.md",
        "ORAL_DEFENSE.md",
        "WORKLOG.md",
        "quality/FINAL_CHECK.yaml",
        "quality/QUALITY_REVIEW.yaml",
        "quality/RENDER_MANIFEST.yaml",
        "build/final-candidate.pdf",
    ),
}

TEXT_SUFFIXES = {".md", ".tex", ".yaml", ".yml", ".json", ".csv", ".txt", ".dat", ".py"}


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
    path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _file_digest(path: Path) -> str:
    if path.suffix.lower() in TEXT_SUFFIXES:
        payload = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    else:
        payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest()


def gate_files(experiment: Path, gate: str) -> list[Path]:
    files: list[Path] = []
    for relative in GATE_PATHS[gate]:
        candidate = experiment / relative
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                item for item in candidate.rglob("*")
                if item.is_file() and item.name != ".gitkeep" and "rendered" not in item.parts
            )
    return sorted(set(files), key=lambda item: item.relative_to(experiment).as_posix())


def gate_manifest(experiment: Path, gate: str) -> list[dict[str, object]]:
    manifest = [
        {
            "path": path.relative_to(experiment).as_posix(),
            "sha256": _file_digest(path),
            "bytes": path.stat().st_size,
        }
        for path in gate_files(experiment, gate)
    ]
    # build/ is intentionally ignored by Git. After release, a clean clone can
    # therefore use the byte-identical released PDF as the logical candidate
    # artifact when verifying the recorded G3 approval.
    if gate == "G3" and not any(item["path"] == "build/final-candidate.pdf" for item in manifest):
        released = experiment / "deliverables" / "report.pdf"
        if released.is_file():
            manifest.append({
                "path": "build/final-candidate.pdf",
                "sha256": _file_digest(released),
                "bytes": released.stat().st_size,
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
    return True, "approved and current"


def require_prior_approvals(experiment: Path, gate: str) -> list[str]:
    errors: list[str] = []
    for prior in GATES[: GATES.index(gate)]:
        ok, reason = approval_current(experiment, prior)
        if not ok:
            errors.append(reason)
    return errors
