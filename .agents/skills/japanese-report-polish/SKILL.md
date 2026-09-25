---
name: japanese-report-polish
description: 技術内容が確定した日本語実験レポートを、数値・式・引用・断定度を変えずに推敲する。PHASE 7でのみ使用する。
---

# 日本語実験レポート推敲

1. ルートの `ANTIGRAVITY.md` を全文読む。
2. 対象実験がPHASE 6合格済みか確認する。
3. `python scripts/polish_guard.py snapshot <experiment>` を実行する。
4. Codexが指定した本文ファイルだけを推敲する。
5. 技術的疑問は変更せず `QUESTIONS.md` に記録する。
6. `python scripts/polish_guard.py verify <experiment>` を実行する。
7. `WORKLOG.md` に変更範囲を記録し、Codexへ再監査を依頼する。

保護対象の差分が検出された場合、基準ファイルを更新して通過させてはならない。編集を戻すかCodexへ返す。
