"""Show prose changes and record an explicit review of the exact two versions."""
from __future__ import annotations

import argparse
import difflib
import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import yaml

from workflow_core import content_fingerprint
from tex_sources import strip_comments


def quantities(text: str, *, tex: bool = False) -> tuple[tuple[str, ...], tuple[str, ...]]:
    text = unicodedata.normalize("NFKC", strip_comments(text) if tex else text)
    text = re.sub(r"\\(?:sourcecite|ref|eqref|cite)\{[^}]*\}", "", text)
    text = re.sub(r"(?:図|表|式|リスト)\s*\(?\d+\)?", "", text)
    text = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", text)
    numbers = tuple(str(Decimal(m.group()).normalize()) for m in re.finditer(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text))
    # Preserve order so swapping two reported measurements is also detected.
    text = text.replace(r"\%", "%")
    units = tuple(re.findall(r"(?<![A-Za-z])(?:ms|ns|s|mm|cm|m|kg|g|Hz|kHz|MHz|V|A|W|Pa|K|mol|%)(?![A-Za-z])", text))
    return numbers, units


def paths(experiment: Path, slot: dict) -> tuple[Path, Path]:
    slot_id = slot["slot_id"]
    expected = (f"prose/original/{slot_id}.md", f"prose/typeset/{slot_id}.tex")
    if (slot.get("original_file"), slot.get("typeset_file")) != expected:
        raise ValueError(f"prose paths must match slot {slot_id}")
    return tuple(experiment / name for name in expected)


def review_errors(experiment: Path, slot: dict) -> list[str]:
    original, typeset = paths(experiment, slot)
    if not original.is_file() or not typeset.is_file():
        return []  # Missing files are diagnosed by the phase validator.
    review = slot.get("review") or {}
    errors = []
    if review.get("original_sha256") != content_fingerprint(original)[0] or review.get("typeset_sha256") != content_fingerprint(typeset)[0]:
        errors.append("prose review is missing or stale")
    changed = quantities(original.read_text(encoding="utf-8")) != quantities(typeset.read_text(encoding="utf-8"), tex=True)
    if changed and slot.get("semantic_change") != "user_approved":
        errors.append("numbers or units changed without user approval")
    if slot.get("semantic_change") == "user_approved":
        if review.get("status") != "user_approved" or not str(review.get("decision_text", "")).startswith(f"承認 {slot['slot_id']}:"):
            errors.append("meaning change needs a version-bound user decision")
    elif review.get("status") != "meaning_unchanged" or not review.get("note"):
        errors.append("meaning-preservation review is not recorded")
    references = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", strip_comments(typeset.read_text(encoding="utf-8"))))
    if references - set(slot.get("planned_references", [])):
        errors.append("reference target differs from the approved writing plan")
    return errors


def write_diff(experiment: Path, plan: dict) -> Path:
    lines = ["# 本人原文と組版後本文の差分", "", "組版表記も差分に含む。数値・単位・因果・断定・結論を確認する。意味の同一性は機械だけでは判定できない。", ""]
    for slot in plan["slots"]:
        original, typeset = paths(experiment, slot)
        if not original.is_file() or not typeset.is_file():
            continue
        left, right = original.read_text(encoding="utf-8"), typeset.read_text(encoding="utf-8")
        if left != right:
            lines.extend([f"## {slot['display_label']} ({slot['slot_id']})", "", "```diff", *difflib.unified_diff(left.splitlines(), right.splitlines(), fromfile="本人原文", tofile="組版後", lineterm=""), "```", ""])
    path = experiment / "quality/PROSE_DIFF.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def record_review(experiment: Path, slot_id: str, note: str, decision: str | None = None) -> None:
    path = experiment / "spec/WRITING_PLAN.yaml"
    plan = yaml.safe_load(path.read_text(encoding="utf-8"))
    slot = next(item for item in plan["slots"] if item["slot_id"] == slot_id)
    original, typeset = paths(experiment, slot)
    original_hash = content_fingerprint(original)[0]
    if slot.get("original_sha256") and slot["original_sha256"] != original_hash:
        raise ValueError("original user prose changed: preserve the received version and verify the new user receipt before reviewing")
    if not note.strip():
        raise ValueError("review note is required")
    if decision is not None and not decision.startswith(f"承認 {slot_id}:"):
        raise ValueError(f"decision must start with 承認 {slot_id}:")
    if decision is None and quantities(original.read_text(encoding="utf-8")) != quantities(typeset.read_text(encoding="utf-8"), tex=True):
        raise ValueError("numbers or units changed; show diff and request user approval")
    slot["original_sha256"] = original_hash
    slot["status"] = "typeset"
    slot["semantic_change"] = "user_approved" if decision else "none"
    slot["proofread_notes"] = note
    slot["review"] = {"original_sha256": slot["original_sha256"], "typeset_sha256": content_fingerprint(typeset)[0],
                      "status": "user_approved" if decision else "meaning_unchanged", "decision_text": decision,
                      "note": note, "reviewed_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    plan["status"] = "prose_complete" if all(item["status"] == "typeset" for item in plan["slots"]) else "prose_partial"
    path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
    write_diff(experiment, plan)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--slot", help="record review after reading original and typeset text")
    parser.add_argument("--note")
    parser.add_argument("--decision", help="exact user response: 承認 P-xxx: reason")
    args = parser.parse_args()
    experiment = args.experiment.resolve()
    if args.slot:
        record_review(experiment, args.slot, args.note or "", args.decision)
    print(write_diff(experiment, yaml.safe_load((experiment / "spec/WRITING_PLAN.yaml").read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
