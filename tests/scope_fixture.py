"""Declared boundaries for synthetic tests; not a real teaching assessment."""
from pathlib import Path
import yaml


def task():
    return {"task_id": "TASK-001", "title": "架空の計測例", "instruction_scope": "I-001 全文（架空例）",
            "prior_task_ids": [], "allowed_knowledge": ["提供された架空データの集計と基礎的な計算量"],
            "excluded_knowledge": ["後続課題の結果を既知として利用しない"], "requirement_ids": ["REQ-001"],
            "submission_code": [], "helper_code": ["analysis/analyze.py"],
            "comment_policy": "集計条件と単位変換の意図を説明する。架空試験用の設定。"}


def reviews():
    return [{"task_id": "TASK-001", "status": "passed", "evidence": "テスト用固定記録: report/sections/02-method.tex と analysis/analyze.py。実在授業の評価ではない。"}]


def set_field(experiment: Path, relative: str, key: str, value):
    path = experiment / relative
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data[key] = value
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
