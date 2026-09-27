# HANDOFF

## 実施内容

- TODO

## 重視した点と判断根拠

- TODO

## 実験結果

- TODO

## レポートへの反映

- TODO

## 本文の本人執筆確認

- 原文保存先: `prose/original/`
- 組版済み本文: `prose/typeset/`
- 意味を変える修正の承認状況: TODO

## 教授視点評価

- `PROFESSOR_EVALUATION.md` を参照

## ユーザー確認事項・未解決事項

- TODO

## 再生成方法

```powershell
python scripts/reproduce.py verify experiments/<id>
python scripts/build_report.py experiments/<id> --mode candidate
# G3承認後のみ
python scripts/workflow.py release experiments/<id>
```

## 提出ファイル

- `deliverables/report.pdf`
- `deliverables/HANDOFF.md`
- `deliverables/PROFESSOR_EVALUATION.md`
- `deliverables/SOURCE_AUDIT.md`
- `deliverables/RESULT_TRACEABILITY.md`
- `deliverables/WORKLOG.md`

`PROFESSOR_EVALUATION.md` は本人確認用であり、教員から指定されない限りレポートと一緒に提出しない。採点対応表や口頭試問資料は必要な場合だけ追加する。
