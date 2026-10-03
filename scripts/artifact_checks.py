"""Bind build inputs, PDFs and reviews to the same revision."""
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from workflow_core import content_fingerprint, gate_fingerprint, manifest_digest


def manifest_path(experiment: Path, mode: str) -> Path:
    return experiment / "quality" / f"{mode.upper()}_BUILD.yaml"


def build_inputs(experiment: Path, mode: str, dependencies: list[str] | None = None) -> list[dict]:
    root = Path(__file__).resolve().parents[1]
    scopes = [("experiment", experiment, (
        "report", "data/processed", "analysis", "spec/REPORT_META.yaml",
        "spec/STYLE_OVERRIDES.yaml", "spec/WRITING_PLAN.yaml",
    )), ("framework", root, ("tex", "config/style-contract.yaml"))]
    if mode != "skeleton":
        scopes[0] = ("experiment", experiment, (*scopes[0][2], "prose"))
    result = []
    for scope, base, relatives in scopes:
        files = set()
        for relative in relatives:
            path = base / relative
            if path.is_file():
                files.add(path)
            elif path.is_dir():
                files.update(p for p in path.rglob("*") if p.is_file())
        for path in sorted(files):
            if path.name == ".gitkeep" or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            # Receipt/review metadata does not change what is typeset.
            digest, size = gate_fingerprint(experiment, "G2", path) if path.name == "WRITING_PLAN.yaml" else content_fingerprint(path)
            result.append({"path": f"{scope}/{path.relative_to(base).as_posix()}", "sha256": digest, "bytes": size})
    known = {item["path"] for item in result}
    for relative in dependencies or []:
        path = (experiment / relative).resolve()
        path.relative_to(experiment.resolve())
        key = f"experiment/{relative}"
        if key not in known:
            digest, size = content_fingerprint(path)
            result.append({"path": key, "sha256": digest, "bytes": size})
            known.add(key)
    return sorted(result, key=lambda item: item["path"])


def record_build(experiment: Path, mode: str, pdf: Path, dependencies: list[str] | None = None) -> dict:
    inputs = build_inputs(experiment, mode, dependencies)
    record = {"version": 1, "mode": mode, "inputs_digest": manifest_digest(inputs),
              "inputs": inputs, "dependencies": dependencies or [], "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
    path = manifest_path(experiment, mode)
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(record, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
    return record


def verify_build(experiment: Path, mode: str, pdf: Path | None = None) -> dict:
    path = manifest_path(experiment, mode)
    if not path.is_file():
        raise ValueError(f"{mode} build manifest is missing; rebuild the PDF")
    record = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("mode") != mode or record.get("version") != 1:
        raise ValueError(f"invalid {mode} build manifest")
    current = build_inputs(experiment, mode, record.get("dependencies", []))
    if record.get("inputs_digest") != manifest_digest(current) or record.get("inputs_digest") != manifest_digest(record.get("inputs", [])):
        raise ValueError(f"{mode} PDF is stale: build inputs changed; rebuild and review")
    if pdf is not None:
        if not pdf.is_file() or record.get("pdf_sha256") != hashlib.sha256(pdf.read_bytes()).hexdigest():
            raise ValueError(f"{mode} PDF does not match its build manifest")
    return record


def recorder_dependencies(experiment: Path) -> list[str]:
    recorder = experiment / "build/main.fls"
    if not recorder.is_file():
        raise ValueError("TeX recorder is missing; use latexmk with -recorder")
    paths = set()
    for line in recorder.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("INPUT "):
            continue
        path = (experiment / "report" / line[6:].strip('"')).resolve()
        try:
            relative = path.relative_to(experiment.resolve())
        except ValueError:
            continue  # TeX installation and fonts are verified through the PDF.
        if relative.parts[0] not in {"build", "quality", "workflow", "deliverables"} and path.is_file():
            paths.add(relative.as_posix())
    return sorted(paths)
