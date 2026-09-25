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
- ユーザーはG1・G2・G3の3回で、本人にしか確認できない事実と採否を判断する。各承認は対象ファイルのハッシュへ結び付くため、後から内容が変われば自動失効する。
- Pythonスクリプトはハッシュ、スキーマ、数値対応、再生成、PDF技術条件を機械検査する。課題の意味、結果の解釈、論証、資料内容の評価にはCodexが必要であり、本人性の確認はユーザーだけが行う。

詳細は [設計根拠](rules/00-design-basis.md) と [PHASE 0〜8](rules/70-workflow-gates.md) を参照してください。

ディレクトリ構成、各YAML項目、レポート様式、全Phaseの具体的な進め方、検査内容、トラブル時の判断は [詳細利用ガイド](docs/USER_GUIDE.md) にまとめています。

## 新しい実験を始める

Python 3.10 以上が必要です。依存ライブラリは `python -m pip install -r requirements.txt` で導入します。TeX をビルドする場合は LuaLaTeX と latexmk も使います。

```powershell
python scripts/new_experiment.py example-id --title "実験題目"
python scripts/validate_experiment.py experiments/example-id --phase 0
```

`experiments/example-id/instructions/` に実習書を置き、**実習書を全ページ読んでから** `QUESTIONS.md` を作成します。ユーザー回答を `spec/USER_DECISIONS.yaml` に保存し、G1を承認するまで実験を開始しません。

```powershell
python scripts/workflow.py refresh-context experiments/example-id
python scripts/workflow.py prepare-review experiments/example-id --gate G1
# ユーザーが確認票を読み、チャットで「承認 G1」と回答した後だけ実行
python scripts/workflow.py approve experiments/example-id --gate G1 --decision "承認 G1"
```

実験後は生データを封印し、分析結果を別環境で再生成できることを確認してからG2へ進みます。

```powershell
python scripts/workflow.py seal-data experiments/example-id
python scripts/reproduce.py seal experiments/example-id
python scripts/workflow.py prepare-review experiments/example-id --gate G2
# 「承認 G2」の本人回答後に approve を実行
```

G2後に執筆・Antigravity推敲・Codex再監査を行い、最終候補を作ります。候補と提出版は別物です。

```powershell
python scripts/build_report.py experiments/example-id --mode candidate
python scripts/render_pdf.py experiments/example-id/build/final-candidate.pdf experiments/example-id/quality/rendered --dpi 180 --manifest experiments/example-id/quality/RENDER_MANIFEST.yaml
python scripts/workflow.py prepare-review experiments/example-id --gate G3
# 「承認 G3」の本人回答後だけ提出版へ昇格
python scripts/workflow.py release experiments/example-id
```

`build/draft.pdf` は作業用、`build/final-candidate.pdf` は本人確認用、`deliverables/report.pdf` だけがG3承認済みの提出版です。

## PHASE 0〜8

| Phase | 目的 | 完了条件の要約 |
|---:|---|---|
| 0 | 受領・保全 | 実習書と入力物の一覧、ハッシュ、欠落確認 |
| 1 | 要求理解・事前質問 | 実習書全読、`QUESTIONS.md`、回答済み `USER_DECISIONS.yaml` |
| 2 | 実験計画・G1 | 手順、変数、反復回数、停止条件、分析法を本人が承認 |
| 3 | 実験実行 | 生データを不変保存し、環境と逸脱を記録 |
| 4 | 分析 | 生データから再現可能な処理で表・図・統計量を生成 |
| 5 | 出典検証・G2 | 各外部主張と出典本文の対応、証拠と論証方針を本人が承認 |
| 6 | 執筆・TeX | 規則に沿って本文と図表を作成 |
| 7 | 日本語推敲・再監査 | Antigravity 推敲後に Codex が意味・数値・引用を再検証 |
| 8 | G3・提出物固定 | 最終候補を本人が承認した後だけ提出版へ昇格 |

ゲートの具体的な必須項目は `rules/70-workflow-gates.md` と `scripts/validate_experiment.py` が正です。

## サンプル

`examples/sort-benchmark/` に、架空データを用いた完成例があります。内容はテンプレートの表示確認用であり、実在する学生の成果物ではありません。

## 根拠資料

共通規則の作成時には、情報処理学会の原稿執筆案内、北里大学、名古屋大学、愛媛大学の公開資料を実際に開いて該当箇所を確認しました。どの資料から何を採用し、何を採用しなかったかは `rules/00-design-basis.md` に記録しています。
