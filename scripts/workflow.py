#!/usr/bin/env python3
"""Manage the three human approval gates without calling an LLM."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from workflow_core import (
    GATES,
    GATE_TITLES,
    approval_current,
    gate_digest,
    load_state,
    require_prior_approvals,
    review_path,
    state_path,
    write_state,
)


GATE_PHASE = {"G1": 2, "G2": 5, "G3": 8}


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def initial_state(example: bool = False) -> dict:
    return {
        "version": 1,
        "current_gate": "G1",
        "status": "preparing",
        "example_only": example,
        "gates": {
            gate: {
                "status": "pending",
                "prepared_at": None,
                "decided_at": None,
                "decided_by": None,
                "decision_text": None,
                "artifact_digest": None,
                "artifact_count": 0,
                "review_file": f"workflow/{gate}_REVIEW.md",
            }
            for gate in GATES
        },
    }


def run_validation(experiment: Path, gate: str) -> None:
    command = [
        sys.executable,
        str(repo_root() / "scripts" / "validate_experiment.py"),
        str(experiment),
        "--phase",
        str(GATE_PHASE[gate]),
    ]
    if gate == "G3":
        command.append("--candidate")
    subprocess.run(command, cwd=repo_root(), check=True)
    if gate == "G2":
        subprocess.run(
            [sys.executable, str(repo_root() / "scripts" / "reproduce.py"), "verify", str(experiment)],
            cwd=repo_root(),
            check=True,
        )


def limited(items: list[str], maximum: int = 5) -> list[str]:
    result = items[:maximum]
    if len(items) > maximum:
        result.append(f"ほか{len(items) - maximum}件（詳細ファイルを参照）")
    return result


def packet_g1(experiment: Path) -> list[str]:
    req = load_yaml(experiment / "spec" / "ASSIGNMENT_REQUIREMENTS.yaml")
    plan = load_yaml(experiment / "spec" / "EXPERIMENT_PLAN.yaml")
    meta = load_yaml(experiment / "spec" / "REPORT_META.yaml")
    integrity = load_yaml(experiment / "spec" / "ACADEMIC_INTEGRITY.yaml")
    assignment = req.get("assignment", {})
    lines = [
        f"- 科目・課題: {assignment.get('course')} / {assignment.get('title')}",
        f"- 提出形式・確認項目: {assignment.get('submission_format')} / 要求{len(req.get('requirements', []))}件・採点基準{len(req.get('rubric_criteria', []))}件",
        f"- AI利用状態: {integrity.get('ai_use', {}).get('status')}",
        f"- 実験目的: {plan.get('objective')}",
        f"- 反復回数: {plan.get('replications')}、表紙項目数: {len(meta.get('cover', {}).get('fields', []))}",
    ]
    return lines


def packet_g2(experiment: Path) -> list[str]:
    manifest = load_yaml(experiment / "spec" / "EXECUTION_MANIFEST.yaml")
    claims = load_yaml(experiment / "spec" / "CLAIMS.yaml").get("claims", [])
    sources = load_yaml(experiment / "spec" / "SOURCES.yaml").get("sources", [])
    deviations = [str(run.get("deviation")) for run in manifest.get("runs", []) if run.get("deviation")]
    result_text = (experiment / "RESULT_TRACEABILITY.md").read_text(encoding="utf-8")
    result_ids = sorted(set(__import__("re").findall(r"\bR-[0-9]{3}\b", result_text)))
    return [
        f"- 実行数: {len(manifest.get('runs', []))}",
        f"- 主要結果: {', '.join(result_ids)}",
        f"- 主張数: {len(claims)}、検証済み出典数: {len(sources)}",
        f"- 計画逸脱: {'; '.join(limited(deviations, 3)) if deviations else 'なし'}",
        "- 詳細: RESULT_TRACEABILITY.md、SOURCE_AUDIT.md、spec/CLAIMS.yaml",
    ]


def packet_g3(experiment: Path) -> list[str]:
    quality = load_yaml(experiment / "quality" / "QUALITY_REVIEW.yaml")
    final = load_yaml(experiment / "quality" / "FINAL_CHECK.yaml")
    rubric = quality.get("rubric", [])
    failed = [item.get("rubric_id") for item in rubric if item.get("status") == "failed"]
    pdf = experiment / "build" / "final-candidate.pdf"
    return [
        f"- 最終候補PDF: {pdf.relative_to(experiment).as_posix()} ({pdf.stat().st_size} bytes)",
        f"- 採点基準: {len(rubric)}件、失敗: {', '.join(failed) if failed else 'なし'}",
        f"- 視覚確認: {final.get('visual_review', {}).get('status')}",
        f"- 技術確認: {final.get('technical_review', {}).get('status')}",
        "- 詳細: HANDOFF.md、quality/QUALITY_REVIEW.yaml",
    ]


PACKET_BUILDERS = {"G1": packet_g1, "G2": packet_g2, "G3": packet_g3}
USER_CHECKS = {
    "G1": [
        "課題の解釈、提出条件、表紙情報に誤りがないか。",
        "AI利用範囲が授業規則に反していないか。",
        "実験条件、反復回数、除外基準を実際に実行できるか。",
    ],
    "G2": [
        "生データが実際に行った実験・作業のものか。",
        "失敗、除外、再実験、環境情報に誤りがないか。",
        "主要結果と考察の方向を本人の認識として採用してよいか。",
    ],
    "G3": [
        "氏名、学生番号、科目名、日付が正しいか。",
        "PDFの見た目、図表、文字、改ページに問題がないか。",
        "実際にしていないことや、自分で説明できない記述がないか。",
        "この最終候補を提出用PDFへ確定してよいか。",
    ],
}


def build_review(experiment: Path, gate: str, manifest: list[dict]) -> str:
    lines = [
        f"# {gate}: {GATE_TITLES[gate]}の確認",
        "",
        "## 推奨判断",
        "",
        "自動検査は合格済み。下記の本人確認に問題がなければ承認してください。",
        "",
        "## 要約",
        "",
        *PACKET_BUILDERS[gate](experiment),
        "",
        "## あなたに確認してほしいこと",
        "",
        *[f"{index}. {item}" for index, item in enumerate(USER_CHECKS[gate], 1)],
        "",
        "## 技術記録",
        "",
        f"対象{len(manifest)}ファイルの内容を固定しました。照合値は `workflow/STATE.yaml` に保存されています。",
        "",
        "## 回答方法",
        "",
        f"問題がなければ `承認 {gate}`、修正が必要なら `修正 {gate}: <内容>` と回答してください。",
        "",
    ]
    return "\n".join(lines)


def release(experiment: Path) -> None:
    for gate in GATES:
        ok, reason = approval_current(experiment, gate)
        if not ok:
            raise RuntimeError(reason)
    candidate = experiment / "build" / "final-candidate.pdf"
    if not candidate.is_file():
        raise RuntimeError("final candidate PDF is missing")
    deliverables = experiment / "deliverables"
    deliverables.mkdir(exist_ok=True)
    shutil.copy2(candidate, deliverables / "report.pdf")
    for name in [
        "HANDOFF.md",
        "SOURCE_AUDIT.md",
        "RESULT_TRACEABILITY.md",
        "WORKLOG.md",
    ]:
        shutil.copy2(experiment / name, deliverables / name)
    # 課程や本人の希望に応じた補助資料は、存在する場合だけ同梱する。
    for name in ["RUBRIC_TRACEABILITY.md", "ORAL_DEFENSE.md"]:
        optional = experiment / name
        if optional.is_file():
            shutil.copy2(optional, deliverables / name)
        else:
            (deliverables / name).unlink(missing_ok=True)
    # v4以前に提出物へ複製していた内部監査ファイルを残さない。
    (deliverables / "QUALITY_REVIEW.yaml").unlink(missing_ok=True)
    subprocess.run(
        [sys.executable, str(repo_root() / "scripts" / "validate_experiment.py"), str(experiment), "--phase", "8"],
        cwd=repo_root(),
        check=True,
    )
    state = load_state(experiment)
    state["current_gate"] = "complete"
    state["status"] = "released"
    state["released_at"] = now()
    state["release_sha256"] = hashlib.sha256((deliverables / "report.pdf").read_bytes()).hexdigest()
    write_state(experiment, state)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init")
    init_parser.add_argument("experiment", type=Path)
    init_parser.add_argument("--example", action="store_true")
    status_parser = sub.add_parser("status")
    status_parser.add_argument("experiment", type=Path)
    review_parser = sub.add_parser("prepare-review")
    review_parser.add_argument("experiment", type=Path)
    review_parser.add_argument("--gate", choices=GATES, required=True)
    approve_parser = sub.add_parser("approve")
    approve_parser.add_argument("experiment", type=Path)
    approve_parser.add_argument("--gate", choices=GATES, required=True)
    approve_parser.add_argument("--decision", required=True)
    approve_parser.add_argument("--migration-example", action="store_true")
    release_parser = sub.add_parser("release")
    release_parser.add_argument("experiment", type=Path)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("experiment", type=Path)
    context_parser = sub.add_parser("refresh-context")
    context_parser.add_argument("experiment", type=Path)
    seal_parser = sub.add_parser("seal-data")
    seal_parser.add_argument("experiment", type=Path)

    args = parser.parse_args()
    experiment = args.experiment.resolve()
    if not experiment.is_dir():
        parser.error(f"not a directory: {experiment}")

    if args.command == "init":
        if state_path(experiment).exists():
            parser.error("workflow state already exists")
        write_state(experiment, initial_state(args.example))
        print(state_path(experiment))
        return 0

    state = load_state(experiment)
    if args.command == "refresh-context":
        path = experiment / "spec" / "CONTEXT_INDEX.yaml"
        data = load_yaml(path)
        for document in data.get("documents", []):
            target = (experiment / document["path"]).resolve()
            try:
                target.relative_to(experiment)
            except ValueError as exc:
                raise RuntimeError(f"context path escapes experiment: {document['path']}") from exc
            if not target.is_file():
                raise FileNotFoundError(document["path"])
            document["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
            newline="\n",
        )
        print(path)
        return 0

    if args.command == "seal-data":
        path = experiment / "spec" / "EXECUTION_MANIFEST.yaml"
        data = load_yaml(path)
        for run in data.get("runs", []):
            for raw_file in run.get("raw_files", []):
                target = (experiment / raw_file["path"]).resolve()
                try:
                    target.relative_to(experiment)
                except ValueError as exc:
                    raise RuntimeError(f"raw path escapes experiment: {raw_file['path']}") from exc
                if not target.is_file():
                    raise FileNotFoundError(raw_file["path"])
                raw_file["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
                raw_file["bytes"] = target.stat().st_size
        data["sealed_at"] = now()
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
            newline="\n",
        )
        print(path)
        return 0

    if args.command == "status":
        print(f"現在: {state.get('current_gate')} / {state.get('status')}")
        for gate in GATES:
            ok, reason = approval_current(experiment, gate)
            print(f"{gate}: {'有効' if ok else state['gates'][gate]['status']} - {reason}")
        return 0

    if args.command == "prepare-review":
        errors = require_prior_approvals(experiment, args.gate)
        if errors:
            raise RuntimeError("; ".join(errors))
        run_validation(experiment, args.gate)
        digest, manifest = gate_digest(experiment, args.gate)
        packet = review_path(experiment, args.gate)
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(
            build_review(experiment, args.gate, manifest),
            encoding="utf-8",
            newline="\n",
        )
        gate_state = state["gates"][args.gate]
        gate_state.update({
            "status": "awaiting_user",
            "prepared_at": now(),
            "decided_at": None,
            "decided_by": None,
            "decision_text": None,
            "artifact_digest": digest,
            "artifact_count": len(manifest),
            "artifacts": manifest,
        })
        state["current_gate"] = args.gate
        state["status"] = "awaiting_user"
        write_state(experiment, state)
        print(packet)
        return 0

    if args.command == "approve":
        gate_state = state["gates"][args.gate]
        if gate_state.get("status") != "awaiting_user":
            raise RuntimeError(f"{args.gate} is not awaiting user approval")
        current, manifest = gate_digest(experiment, args.gate)
        if current != gate_state.get("artifact_digest"):
            raise RuntimeError("reviewed artifacts changed; prepare a new review packet")
        expected = f"承認 {args.gate}"
        if not args.decision.strip().startswith(expected):
            raise RuntimeError(f"approval decision must start with '{expected}'")
        if args.migration_example and not state.get("example_only"):
            raise RuntimeError("migration approval is allowed only for an example workflow")
        gate_state.update({
            "status": "approved",
            "decided_at": now(),
            "decided_by": "framework_migration" if args.migration_example else "user",
            "decision_text": args.decision,
            "artifact_digest": current,
            "artifact_count": len(manifest),
            "artifacts": manifest,
        })
        index = GATES.index(args.gate)
        state["current_gate"] = GATES[index + 1] if index + 1 < len(GATES) else "complete"
        state["status"] = "executing" if args.gate != "G3" else "approved"
        write_state(experiment, state)
        print(f"{args.gate}を承認済みとして記録しました。")
        return 0

    if args.command == "verify":
        failed = False
        for gate in GATES:
            if state["gates"][gate]["status"] == "approved":
                ok, reason = approval_current(experiment, gate)
                print(f"{gate}: {'PASS' if ok else 'FAIL'} - {reason}")
                failed = failed or not ok
        return 1 if failed else 0

    if args.command == "release":
        release(experiment)
        print(experiment / "deliverables" / "report.pdf")
        return 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
