#!/usr/bin/env python3
"""Manage the three human approval gates without calling an LLM."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
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
from review_prose import write_diff
from artifact_checks import verify_build


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
    if gate == "G2":
        command.append("--skeleton")
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
    rubric_source = req.get("rubric_source", {})
    lines = [
        f"- 科目・課題・表紙: {assignment.get('course')} / {assignment.get('title')} / " + "、".join(f"{item['label']}: {item['value']}" for item in meta.get('cover', {}).get('fields', [])),
        f"- 提出条件: {assignment.get('submission_format')} / 期限: {assignment.get('deadline')} / " + "；".join(f"{item['requirement_id']}: {item['description']}（{item['source_locator']}）" for item in req.get('requirements', [])),
        f"- 採点基準: {rubric_source.get('status')} / " + "；".join(f"{item['rubric_id']}: {item['criterion']} / 合格条件: {'、'.join(item['acceptance_criteria'])}（{item['source_locator']}）" for item in req.get('rubric_criteria', [])),
        f"- AI利用状態: {integrity.get('ai_use', {}).get('status')} / 本文: 本人執筆のみ",
        f"- 推奨実験計画: {plan.get('objective')} / {plan.get('replications')}回 / 条件: {plan.get('independent_variables')} / 除外: {plan.get('exclusion_rules')} / 停止: {plan.get('stop_conditions')}（詳細: spec/EXPERIMENT_PLAN.yaml）",
    ]
    return lines


def packet_g2(experiment: Path) -> list[str]:
    manifest = load_yaml(experiment / "spec" / "EXECUTION_MANIFEST.yaml")
    claims = load_yaml(experiment / "spec" / "CLAIMS.yaml").get("claims", [])
    sources = load_yaml(experiment / "spec" / "SOURCES.yaml").get("sources", [])
    deviations = [str(run.get("deviation")) for run in manifest.get("runs", []) if run.get("deviation")]
    result_text = (experiment / "RESULT_TRACEABILITY.md").read_text(encoding="utf-8")
    result_ids = sorted(set(__import__("re").findall(r"\bR-[0-9]{3}\b", result_text)))
    writing = load_yaml(experiment / "spec" / "WRITING_PLAN.yaml")
    return [
        f"- 実行数: {len(manifest.get('runs', []))}",
        f"- 主要結果: {', '.join(result_ids)}（値・算出方法: RESULT_TRACEABILITY.md）",
        f"- 主張数: {len(claims)}、検証済み出典数: {len(sources)}、文章枠: {len(writing.get('slots', []))}",
        f"- 計画逸脱: {'; '.join(limited(deviations, 3)) if deviations else 'なし'}",
        "- 骨格PDF: build/skeleton.pdf（見出し・図表・式・コード・文章枠を確認）",
    ]


def packet_g3(experiment: Path) -> list[str]:
    quality = load_yaml(experiment / "quality" / "QUALITY_REVIEW.yaml")
    final = load_yaml(experiment / "quality" / "FINAL_CHECK.yaml")
    rubric = quality.get("rubric", [])
    professor = load_yaml(experiment / "quality" / "PROFESSOR_REVIEW.yaml")
    failed = [item.get("rubric_id") for item in rubric if item.get("status") == "failed"]
    pdf = experiment / "build" / "final-candidate.pdf"
    return [
        f"- 最終候補PDF: {pdf.relative_to(experiment).as_posix()} ({pdf.stat().st_size} bytes)",
        f"- 採点基準: {len(rubric)}件、失敗: {', '.join(failed) if failed else 'なし'}",
        f"- 教授視点評価: {professor.get('overall', {}).get('verdict')} / " + (f"{professor['overall']['score_percent']}点（教員配点による計算）" if professor.get('overall', {}).get('score_percent') is not None else "数値採点なし（配点未提供）") + " / 弱点: " + "；".join(professor.get('overall', {}).get('weaknesses', [])),
        f"- PDF検査: 視覚 {final.get('visual_review', {}).get('status')} / 技術 {final.get('technical_review', {}).get('status')}",
        "- 本人原文との差分: quality/PROSE_DIFF.md / 詳細評価: PROFESSOR_EVALUATION.md / 引継ぎ: HANDOFF.md",
    ]


PACKET_BUILDERS = {"G1": packet_g1, "G2": packet_g2, "G3": packet_g3}
USER_CHECKS = {
    "G1": [
        "課題の解釈、提出条件、表紙情報に誤りがないか。",
        "採点基準の抽出内容と、各基準の合格条件に誤りがないか。",
        "AI利用範囲が授業規則に反していないか。",
        "実験条件、反復回数、除外基準を実際に実行できるか。",
    ],
    "G2": [
        "生データが実際に行った実験・作業のものか。",
        "失敗、除外、再実験、環境情報に誤りがないか。",
        "見出し、図表、数式、コード、文章枠の順序が書きたい論理に合うか。",
        "各（文章N）の執筆メモと、主要結果・考察の方向を採用してよいか。",
    ],
    "G3": [
        "氏名、学生番号、科目名、日付が正しいか。",
        "PDFの見た目、図表、文字、改ページに問題がないか。",
        "本文が自分の原文に基づき、意味を変える未承認修正がないか。",
        "教授視点評価の弱点を理解し、それでも提出してよいか。",
        "この最終候補を提出用PDFへ確定してよいか。",
    ],
}


def build_review(experiment: Path, gate: str, manifest: list[dict], previous: list[dict] | None = None) -> str:
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
    if previous:
        before = {item['path']: item['sha256'] for item in previous}
        after = {item['path']: item['sha256'] for item in manifest}
        changed = [key for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)]
        lines.extend(["## 前回確認からの変更", "", *[f"- {name}" for name in changed], ""])
        if not changed:
            lines.append("変更なし。前回の判断材料を再利用できます。")
    return "\n".join(lines)


def release(experiment: Path) -> None:
    for gate in GATES:
        ok, reason = approval_current(experiment, gate)
        if not ok:
            raise RuntimeError(reason)
    candidate = experiment / "build" / "final-candidate.pdf"
    if not candidate.is_file():
        raise RuntimeError("final candidate PDF is missing")
    # Check before touching any previously released report.
    run_validation(experiment, "G3")
    names = [
        "report.pdf",
        "HANDOFF.md",
        "PROFESSOR_EVALUATION.md",
        "SOURCE_AUDIT.md",
        "RESULT_TRACEABILITY.md",
        "WORKLOG.md",
    ]
    for name in ["RUBRIC_TRACEABILITY.md", "ORAL_DEFENSE.md"]:
        if (experiment / name).is_file():
            names.append(name)
    deliverables = experiment / "deliverables"
    with tempfile.TemporaryDirectory(prefix=".release-", dir=experiment) as raw:
        temporary = Path(raw)
        staged = temporary / "new"
        backup_dir = experiment / "build/release-backups"
        backup = backup_dir / temporary.name
        staged.mkdir()
        for name in names:
            source = candidate if name == "report.pdf" else experiment / name
            shutil.copy2(source, staged / name)
            if content_hash(source) != content_hash(staged / name):
                raise RuntimeError(f"release copy differs: {name}")
        had_previous = deliverables.exists()
        if had_previous:
            backup_dir.mkdir(parents=True, exist_ok=True)
            deliverables.rename(backup)
        try:
            staged.rename(deliverables)
            subprocess.run([sys.executable, str(repo_root() / "scripts/validate_experiment.py"), str(experiment), "--phase", "8"], cwd=repo_root(), check=True)
            state = load_state(experiment)
            state.update(current_gate="complete", status="released", released_at=now(), release_sha256=content_hash(deliverables / "report.pdf"))
            write_state(experiment, state)
        except BaseException:
            if deliverables.exists():
                deliverables.rename(temporary / "failed")
            if had_previous:
                backup.rename(deliverables)
            raise


def content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    bind_parser = sub.add_parser("bind-reviews", help="bind completed reviews to the PDF actually read; does not mark any review passed")
    bind_parser.add_argument("experiment", type=Path)

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
    if args.command == "bind-reviews":
        record = verify_build(experiment, "candidate", experiment / "build/final-candidate.pdf")
        for name in ("FINAL_CHECK.yaml", "QUALITY_REVIEW.yaml", "PROFESSOR_REVIEW.yaml"):
            path = experiment / "quality" / name
            data = load_yaml(path)
            data["reviewed_pdf_sha256"] = record["pdf_sha256"]
            data["reviewed_inputs_digest"] = record["inputs_digest"]
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
        print("確認記録を候補PDFと入力の版へ接続しました。評価・確認済み状態は変更していません。")
        return 0
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
        if args.gate == "G3":
            write_diff(experiment, load_yaml(experiment / "spec/WRITING_PLAN.yaml"))
        digest, manifest = gate_digest(experiment, args.gate)
        packet = review_path(experiment, args.gate)
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(
            build_review(experiment, args.gate, manifest, state['gates'][args.gate].get('artifacts')),
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
        errors = require_prior_approvals(experiment, args.gate)
        if errors:
            raise RuntimeError("; ".join(errors))
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
