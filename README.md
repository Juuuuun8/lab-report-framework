# lab-report-framework

大学の理工系実験レポートを、根拠・再現性・追跡可能性を保ちながら作るためのフレームワークです。特定の過去レポートの見た目は継承せず、次の優先順位で判断します。

1. 当該授業の実習書、課題文、教員の指示
2. このリポジトリの共通規則
3. 情報処理学会の執筆作法と、日本の大学が公開する理工系レポート作成指針
4. 一般的な技術文書の慣行

上位の指示と下位の規則が衝突した場合は、上位を採用し、`USER_DECISIONS.yaml` と `WORKLOG.md` に理由を残します。

## 作業ディレクトリ

Codex と Antigravity のどちらも、**このリポジトリのルート**を作業ディレクトリに指定してください。個別実験のディレクトリを直接開くと、共通ルール、スキーマ、検査スクリプトを見落とします。

```text
lab-report-framework/          ← ここを開く
├─ AGENTS.md
├─ ANTIGRAVITY.md
├─ rules/
├─ schemas/
├─ scripts/
├─ tex/
├─ templates/
└─ experiments/
```

## 設計の要点

- A4、1段組、本文10.5pt、本文は明朝、見出しはゴシック、余白25mmを標準とする。
- 表紙はレイアウトだけを共通化し、項目と値は実験ごとに `spec/REPORT_META.yaml` で指定する。
- 表紙の次は本文へ入り、タイトル、氏名、概要、キーワードを再掲しない。
- 図表は本文で先に番号参照し、その後の近傍へ置く。ページ上端または下端へのフロートを基本とし、段落途中へ無理に割り込ませない。
- 図キャプションは下、表とコードリストのキャプションは上。図表内は英語が必要な場合を除き日本語とする。
- 参考文献は、実際に本文を開いて主張との一致を確認したものだけを採用する。優先順位は「日本語一次情報・公的機関・公式文書 → 英語一次情報 → 信頼できる日本語二次資料」。
- レポート本文と同時に、`HANDOFF.md`、`SOURCE_AUDIT.md`、`RESULT_TRACEABILITY.md`、`RUBRIC_TRACEABILITY.md`、`ORAL_DEFENSE.md`、`QUALITY_REVIEW.yaml`、`WORKLOG.md` を完成させる。
- 課題要件、採点基準、主張、実行環境、AI利用条件を構造化し、内容品質と学術的誠実性をPDF生成前のゲートで検査する。
- 共通TeXクラスは `config/style-contract.yaml` で版と正規化ハッシュを固定し、意図しない様式変更を検出する。
- Codex が実験、分析、TeX、技術監査を担当する。Antigravity は日本語推敲だけを担当し、変更後は Codex が再監査する。

詳細は [設計根拠](rules/00-design-basis.md) と [PHASE 0〜8](rules/70-workflow-gates.md) を参照してください。

ディレクトリ構成、各YAML項目、レポート様式、全Phaseの具体的な進め方、検査内容、トラブル時の判断は [詳細利用ガイド](docs/USER_GUIDE.md) にまとめています。

## 新しい実験を始める

Python 3.10 以上が必要です。依存ライブラリは `python -m pip install -r requirements.txt` で導入します。TeX をビルドする場合は LuaLaTeX と latexmk も使います。

```powershell
python scripts/new_experiment.py example-id --title "実験題目"
python scripts/validate_experiment.py experiments/example-id --phase 0
```

`experiments/example-id/instructions/` に実習書を置き、**実習書を全ページ読んでから** `QUESTIONS.md` を作成します。ユーザー回答を `spec/USER_DECISIONS.yaml` に保存し、PHASE 1 のゲートを通過するまで実験を開始しません。

```powershell
python scripts/validate_experiment.py experiments/example-id --phase 1
```

レポートのビルドと全検査は次のコマンドで行います。

```powershell
python scripts/build_report.py experiments/example-id
python scripts/validate_experiment.py experiments/example-id --phase 8
```

`build_report.py` は最初にPHASE 0〜6を再検査するため、未検証の出典、未追跡の主張、未承認の様式変更を含むレポートはビルドできません。

提出物は `experiments/<id>/deliverables/` に集約されます。

## PHASE 0〜8

| Phase | 目的 | 完了条件の要約 |
|---:|---|---|
| 0 | 受領・保全 | 実習書と入力物の一覧、ハッシュ、欠落確認 |
| 1 | 要求理解・事前質問 | 実習書全読、`QUESTIONS.md`、回答済み `USER_DECISIONS.yaml` |
| 2 | 実験計画 | 手順、変数、反復回数、停止条件、分析法を確定 |
| 3 | 実験実行 | 生データを不変保存し、環境と逸脱を記録 |
| 4 | 分析 | 生データから再現可能な処理で表・図・統計量を生成 |
| 5 | 出典検証 | 各外部主張と出典本文の対応を監査 |
| 6 | 執筆・TeX | 規則に沿って本文と図表を作成 |
| 7 | 日本語推敲・再監査 | Antigravity 推敲後に Codex が意味・数値・引用を再検証 |
| 8 | 提出物固定 | PDF、追跡資料、ログ、検査結果を揃えて最終確認 |

ゲートの具体的な必須項目は `rules/70-workflow-gates.md` と `scripts/validate_experiment.py` が正です。

## サンプル

`examples/sort-benchmark/` に、架空データを用いた完成例があります。内容はテンプレートの表示確認用であり、実在する学生の成果物ではありません。

## 根拠資料

共通規則の作成時には、情報処理学会の原稿執筆案内、北里大学、名古屋大学、愛媛大学の公開資料を実際に開いて該当箇所を確認しました。どの資料から何を採用し、何を採用しなかったかは `rules/00-design-basis.md` に記録しています。
