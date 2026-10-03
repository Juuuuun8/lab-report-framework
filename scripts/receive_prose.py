"""Receive user-authored paragraphs; never generate or approve prose."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import tempfile

import yaml

from review_prose import paths, write_diff
from workflow_core import approval_current, content_fingerprint


def receive(experiment: Path, entries: list[dict], receipt: str) -> list[str]:
    """Validate the whole batch before writing; retain old originals and reviews."""
    for gate in ("G1", "G2"):
        ok, reason = approval_current(experiment, gate)
        if not ok:
            raise ValueError(reason)
    if not isinstance(receipt, str) or not receipt.strip():
        raise ValueError("receipt must identify the actual user message")
    if not isinstance(entries, list) or not entries:
        raise ValueError("paragraphs must be a non-empty list")
    plan_path = experiment / "spec/WRITING_PLAN.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    slots = {slot["slot_id"]: slot for slot in plan["slots"]}
    changes, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"slot_id", "text"}:
            raise ValueError("each paragraph needs only slot_id and text")
        slot_id, text = entry["slot_id"], entry["text"]
        if not isinstance(slot_id, str) or slot_id not in slots or slot_id in seen:
            raise ValueError(f"unknown or duplicate slot: {slot_id}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"empty prose: {slot_id}")
        seen.add(slot_id)
        slot = slots[slot_id]
        original, typeset = paths(experiment, slot)
        for target in (original, typeset):
            target.resolve().relative_to(experiment.resolve())
        if slot.get("original_sha256"):
            if not original.is_file() or content_fingerprint(original)[0] != slot["original_sha256"]:
                raise ValueError(f"stored original changed or missing: {slot_id}")
        if original.is_file() and original.read_text(encoding="utf-8") == text:
            continue  # A repeated message must not invalidate a completed review.
        changes.append((slot, original, typeset, text))
    if not changes:
        return []
    history = experiment / "prose/history"
    history.mkdir(parents=True, exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y%m%d-%H%M%S-"), dir=history))
    shutil.copy2(plan_path, archive / "WRITING_PLAN.yaml")
    snapshots = {plan_path: plan_path.read_bytes()}
    for name in ("PROSE_DIFF.md", "PROSE_CHANGES.md"):
        target = experiment / "quality" / name
        snapshots[target] = target.read_bytes() if target.is_file() else None
    try:
        for slot, original, typeset, text in changes:
            for target in (original, typeset):
                snapshots[target] = target.read_bytes() if target.is_file() else None
                if target.is_file():
                    shutil.copy2(target, archive / target.name)
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_text(text, encoding="utf-8", newline="\n")
            # The old typeset version must not leak into a partial draft.
            typeset.unlink(missing_ok=True)
            slot.update(status="user_submitted", original_sha256=content_fingerprint(original)[0],
                        semantic_change="none", proofread_notes=None)
            slot.pop("review", None)
        plan["status"] = "prose_partial"
        (archive / "RECEIPT.yaml").write_text(yaml.safe_dump({
            "received_at": datetime.now().astimezone().isoformat(), "user_message": receipt,
            "slots": [{"slot_id": s["slot_id"], "original_sha256": s["original_sha256"]} for s, *_ in changes],
        }, allow_unicode=True, sort_keys=False), encoding="utf-8")
        plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
        write_diff(experiment, plan)
    except BaseException:
        for target, payload in snapshots.items():
            if payload is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(payload)
        raise
    return [s["slot_id"] for s, *_ in changes]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", type=Path)
    parser.add_argument("batch", type=Path, help="YAML: receipt and paragraphs [{slot_id, text}]")
    args = parser.parse_args()
    data = yaml.safe_load(args.batch.read_text(encoding="utf-8"))
    changed = receive(args.experiment.resolve(), data["paragraphs"], data["receipt"])
    print("受領: " + (", ".join(changed) if changed else "変更なし") + "。本文の校正・意味確認は別途必要です。")


if __name__ == "__main__":
    main()
