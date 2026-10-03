"""Validate declared learning boundaries, not the semantics of student work."""
from pathlib import Path
import re

PLACEHOLDER = re.compile(r"\bTODO\b|指定待ち|未確認|未実施|\{\{.+?\}\}")


def check_tasks(experiment: Path, requirements: dict, state: dict, audit, phase: int) -> None:
    tasks = requirements.get("task_scopes", [])
    if not tasks:
        if state.get("version", 1) >= 2:
            audit.require(False, "TASK SCOPE: task_scopes required for workflow version 2")
        else:
            audit.notes.append("旧形式: 課題別の学習範囲監査は未適用。範囲準拠を確認済みとは扱わない。")
        return
    known_requirements = {r.get("requirement_id") for r in requirements.get("requirements", [])}
    seen = set()
    submissions, helpers = set(), set()
    for task in tasks:
        task_id = task.get("task_id")
        audit.require(task_id not in seen, f"TASK SCOPE: duplicate task {task_id}")
        audit.require(set(task.get("prior_task_ids", [])) <= seen,
                      f"TASK SCOPE: {task_id} depends on a later, unknown or same task")
        seen.add(task_id)
        audit.require(set(task.get("requirement_ids", [])) <= known_requirements,
                      f"TASK SCOPE: {task_id} references unknown requirements")
        audit.require(not PLACEHOLDER.search(str(task)), f"TASK SCOPE: unresolved boundary for {task_id}")
        for key, collection in (("submission_code", submissions), ("helper_code", helpers)):
            for relative in task.get(key, []):
                path = Path(relative)
                try:
                    if path.is_absolute() or ".." in path.parts:
                        raise ValueError("not relative")
                    resolved = (experiment / path).resolve()
                    resolved.relative_to(experiment.resolve())
                except ValueError:
                    audit.require(False, f"TASK SCOPE: unsafe code path: {relative}")
                    continue
                collection.add(resolved)
                if phase >= 5:
                    audit.require(resolved.is_file(), f"TASK SCOPE: missing declared code: {relative}")
    audit.require(not submissions.intersection(helpers), "TASK SCOPE: submission and helper code must be separate files")


def check_reviews(requirements: dict, record: dict, audit, stage: str) -> None:
    tasks = {t["task_id"] for t in requirements.get("task_scopes", [])}
    if not tasks:
        return
    rows = record.get("task_scope_reviews", [])
    ids = [r.get("task_id") for r in rows]
    audit.require(set(ids) == tasks and len(ids) == len(tasks), f"TASK SCOPE: {stage} reviews must cover each task exactly once")
    for row in rows:
        audit.require(row.get("status") == "passed", f"TASK SCOPE: {stage} {row.get('task_id')} is not passed")
        evidence = row.get("evidence", "")
        audit.require(bool(evidence.strip()) and not PLACEHOLDER.search(evidence), f"TASK SCOPE: {stage} needs concrete review evidence")
    if stage == "skeleton":
        covered = set()
        for slot in record.get("slots", []):
            linked = set(slot.get("task_ids", []))
            audit.require(bool(linked) and linked <= tasks, f"TASK SCOPE: slot {slot.get('slot_id')} needs known task_ids")
            covered.update(linked)
        audit.require(covered == tasks, "TASK SCOPE: writing slots do not cover all tasks")
