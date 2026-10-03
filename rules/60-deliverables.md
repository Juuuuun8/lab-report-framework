# 必須成果物

最終レポートだけでは完了としない。G3承認前は `build/final-candidate.pdf` とルートの監査資料を候補として扱い、G3承認後に `workflow.py release` が `deliverables/` へ次を固定する。

## report.pdf

提出用PDF。表紙、本文、参考文献、必要な付録を含む。全ページを画像化して目視確認する。

## HANDOFF.md

ユーザーが最初に読む引き継ぎ文書。何を行ったか、本人原文の保全と意味変更の有無、実験結果、レポートへの反映、未解決事項、再生成方法、提出ファイル一覧を記す。

## PROFESSOR_EVALUATION.md

G1で確定した採点基準に沿う教授視点の模擬評価。基準別の判定、本文位置、根拠、不足、厳しい指摘、改善案、総合評価、評価の限界を記す。点数は教員配点と尺度が揃う場合だけ計算する。本人確認用であり、授業から指定されない限り教員へ提出しない。

## SOURCE_AUDIT.md

本文の外部主張と参考文献の対応表。claim ID、本文位置、出典ID、URL、発行主体、言語、資料種別、確認箇所、内容一致の説明、採否と理由を記す。

## RESULT_TRACEABILITY.md

主要な数値・図表・結論を、生データと分析処理へ結び付ける。

## WORKLOG.md

日時、担当、Phase、入力、実行内容、判断と根拠、生成・変更ファイル、異常、逸脱、相談、回答、検証結果を時系列で記す。

## 任意の補助資料


次は授業指定またはユーザーの希望がある場合だけ提出物へ含める。

- `RUBRIC_TRACEABILITY.md`: 採点項目とレポート位置・証拠の対応を人間向けに一覧化する。
- `ORAL_DEFENSE.md`: 主要な判断、計算、限界、出典選定の想定問答を作る。

## 内部監査資料


`quality/QUALITY_REVIEW.yaml`、`quality/PROFESSOR_REVIEW.yaml`、`quality/FINAL_CHECK.yaml`、`workflow/`、`spec/` はCodexと検査器が使う内部資料であり、通常の提出物へ複製しない。

## 補助成果物

必要に応じて、再現用コード、処理済みデータ、環境情報を含める。通常の技術ログは提出物へ含めず、個人情報や秘密情報も含めない。

`build/draft.pdf`、`build/main.pdf`、`build/final-candidate.pdf` は提出版ではない。`deliverables/report.pdf` だけを提出用と呼んでよい。

## 重複記入を避ける正本

- `SOURCE_AUDIT.md` は `spec/SOURCES.yaml` と `spec/CLAIMS.yaml` から生成する。
- `PROFESSOR_EVALUATION.md` と `QUALITY_REVIEW.yaml` の採点対応は `quality/PROFESSOR_REVIEW.yaml` から生成する。技術チェックの証拠は `QUALITY_REVIEW.yaml` に一度だけ記す。
- `RESULT_TRACEABILITY.md` は数値・算出方法の正本、`WORKLOG.md` は実行と判断の時系列の正本とする。他文書に全文転記しない。
- `HANDOFF.md` は成果物への入口、主要結果の短い要約、未解決事項、再生成方法に絞り、監査表を複製しない。
- 生成マーカーのある資料は正本との一致を検査する。既存の手書き資料を移行する際は独自の注記を正本へ移してから `--replace-legacy` を使い、旧版を保存する。
