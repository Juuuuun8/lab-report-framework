#!/usr/bin/env python3
"""Seal and verify analysis outputs by rerunning declared commands in a copy."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

from workflow_core import content_fingerprint


def digest(path: Path) -> tuple[str, int]:
    return content_fingerprint(path)


def load_spec(experiment: Path) -> tuple[Path, dict]:
    path = experiment / "spec" / "REPRODUCE.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid reproduction spec: {path}")
    return path, data


def safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes experiment: {relative}") from exc
    return candidate


def resolve_argv(argv: list[str]) -> list[str]:
    return [sys.executable if item == "{python}" else item for item in argv]


def seal(experiment: Path, path: Path, spec: dict) -> None:
    for output in spec.get("expected_outputs", []):
        target = safe_path(experiment, output["path"])
        if not target.is_file():
            raise FileNotFoundError(f"expected output is missing: {output['path']}")
        output["sha256"], output["bytes"] = digest(target)
    spec["sealed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    path.write_text(
        yaml.safe_dump(spec, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


def verify_current(experiment: Path, spec: dict) -> None:
    for output in spec.get("expected_outputs", []):
        target = safe_path(experiment, output["path"])
        if not target.is_file():
            raise FileNotFoundError(f"expected output is missing: {output['path']}")
        actual_hash, actual_size = digest(target)
        if actual_hash != output.get("sha256") or actual_size != output.get("bytes"):
            raise RuntimeError(f"current analysis output differs from sealed output: {output['path']}")


def reproduce(experiment: Path, spec: dict) -> None:
    if not spec.get("commands") or not spec.get("expected_outputs"):
        raise ValueError("reproduction needs commands and expected outputs")
    verify_current(experiment, spec)
    with tempfile.TemporaryDirectory(prefix="lab-report-reproduce-") as raw:
        replica = Path(raw) / "experiment"
        shutil.copytree(
            experiment,
            replica,
            ignore=shutil.ignore_patterns("build", "deliverables", "rendered", "POLISH_BASELINE.json"),
        )
        for output in spec["expected_outputs"]:
            target = safe_path(replica, output["path"])
            if target.is_relative_to(replica / "data/raw") or target.suffix == ".py":
                raise ValueError(f"expected output cannot be raw data or code: {output['path']}")
            target.unlink()  # Never reuse an existing generated output.
        for command in spec.get("commands", []):
            cwd = safe_path(replica, command.get("cwd", "."))
            subprocess.run(resolve_argv(command["argv"]), cwd=cwd, check=True)
        for output in spec.get("expected_outputs", []):
            regenerated = safe_path(replica, output["path"])
            if not regenerated.is_file():
                raise FileNotFoundError(f"reproduction did not create: {output['path']}")
            actual_hash, actual_size = digest(regenerated)
            if actual_hash != output.get("sha256") or actual_size != output.get("bytes"):
                raise RuntimeError(f"reproduced output differs: {output['path']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("seal", "verify"))
    parser.add_argument("experiment", type=Path)
    args = parser.parse_args()
    experiment = args.experiment.resolve()
    path, spec = load_spec(experiment)
    if args.mode == "seal":
        seal(experiment, path, spec)
        print(path)
    else:
        reproduce(experiment, spec)
        print("PASS: analysis outputs reproduced exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
