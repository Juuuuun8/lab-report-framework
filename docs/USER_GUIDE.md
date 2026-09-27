# 詳細利用ガイド

## 1. 目的と責任境界

この環境は、学生本人が本文を書き、Codexが実験前の確認、実験支援、分析、出典検証、レポート骨格、TeX組版、品質監査を担当する。成績を保証するものではない。教員指示と採点基準への適合を高い再現性で確認し、数値転記、出典不一致、様式崩れ、AIによる無断代筆を防ぐための仕組みである。

優先順位は次のとおりである。

1. 実習書、課題文、教員の明示指示、採点基準
2. 授業・大学のAI利用規則
3. このリポジトリの共通規則
4. 過去レポートの個人的傾向

過去レポートの見た目は規範にしない。

## 2. 作業ディレクトリ

GitHubからリポジトリを丸ごと取得し、Codexでは必ず次のルートを開く。

```text
lab-report-framework/        ← ここを開く
├─ AGENTS.md
├─ config/
├─ rules/
├─ schemas/
├─ scripts/
├─ templates/
├─ tex/
├─ examples/
└─ experiments/
```

`experiments/<id>/` だけを開くと、ルートの `AGENTS.md` と共通規則を利用できない。

## 3. AIと人間の分担

ユーザーが行うこと:

- 本文の全文章を書く。
- 自分しか知らない実施事実、失敗、除外、個人情報を確認する。
- 採点基準、実験計画、骨格、意味変更、最終提出を判断する。
- 最終PDFを自分でも読み、自分の言葉で説明できるか確認する。

Codexが行うこと:

- 実習書と採点基準の全読、質問整理。
- 実験計画、実験支援、分析、図表・式・コードの準備。
- 外部サイト本文の確認と主張との照合。
- 見出しと文章枠を含む骨格PDFの生成。
- ユーザー原文の保全、誤字脱字確認、TeX組版。
- 数値、引用、論理、様式、PDFの監査。
- 採点基準に沿う教授視点の模擬評価。

Pythonはハッシュ、スキーマ、再生成、ファイル存在、PDF寸法など決定的検査だけを行う。意味理解、出典の妥当性、採点判断はCodexとユーザーが担う。

Antigravityや第二AI校閲は使用しない。

## 4. 最初に渡すもの

可能な限り最初に次を渡す。

- 実習書の全ページ
- 課題文、提出方法、締切
- 採点表・ルーブリック・教員の口頭指示
- AI利用規則
- 配布コード、テンプレート、データ
- 表紙に必要な項目と値
- 使用できる装置、OS、ソフトウェア、時間上の制約

採点基準が見つからない場合、Codexはそれを勝手に教員基準として補わない。一般的な理工系レポート品質を内部基準として提案し、「教員提供ではない」ことをG1で確認する。

## 5. 三つの承認

### G1 実験前確認

Codexは課題と採点基準を全読し、最大5項目の確認票を作る。ユーザーは次を確認する。

- 課題解釈と提出条件
- 採点基準の項目、重み、合格条件、出典位置
- 表紙情報
- AI利用範囲と本文本人執筆の契約
- 実験条件、試行回数、除外基準、安全性

問題なければ `承認 G1` と回答する。G1前に実験は開始しない。

### G2 証拠・骨格確認

Codexは実験・分析・出典検証を終え、次を含む `build/skeleton.pdf` を作る。

- 表紙
- 実習書指定の見出し
- 図、表、数式、コード、参考文献
- 本文を入れる `（文章1）`、`（文章2）` などの枠

各枠には `spec/WRITING_PLAN.yaml` で目的、必須論点、予定する図表参照、Evidence ID、Rubric IDが付く。ユーザーはデータが本人のものか、除外と失敗が正しいか、見出しと図表の順序が意図に合うか、各文章枠の分け方が書きやすいかを確認する。問題なければ `承認 G2` と回答する。

### G3 完成稿・提出確認

全文章の組版、PDF監査、採点基準別の教授視点評価が終わった後に行う。ユーザーは次を確認する。

- 本文が自分の原文に基づくか
- 意味を変える修正が承認済みか
- 氏名、学生番号、科目、日付
- 図表、文字、余白、改ページ
- 自分で説明できない記述がないか
- 教授視点評価の弱点を理解したか
- 提出用へ固定してよいか

問題なければ `承認 G3` と回答する。

## 6. 本文の送り方

G2後、Codexが文章枠ごとに「何をチェックして書くか」を示す。ユーザーは次の形式で送る。

```text
文章1:
ここに自分で書いた文章。

文章2:
ここに自分で書いた文章。
```

一度に全部送っても、数枠ずつ送ってもよい。トークン節約のため、Codexは受領した枠と直接関係する執筆メモ・証拠だけを読む。

保存先:

- 原文: `prose/original/P-001.md`
- 組版後: `prose/typeset/P-001.tex`
- 対応表とハッシュ: `spec/WRITING_PLAN.yaml`

Codexが自動適用できる変更:

- 明白な誤字脱字
- 句読点、全半角、表記揺れ、である調の統一
- TeX特殊文字の処理
- ユーザーが書いた式の数式環境化
- 単位の組版
- 図表・式・参考文献の番号を相互参照へ変換
- 確定済み出典への引用コマンド挿入

本人承認が必要な変更:

- 数値、符号、単位、有効数字の変更
- 事実、条件、因果関係、比較方向の変更
- 結論、断定の強さ、適用範囲の変更
- 新しい説明、主張、参考文献の追加
- 本人が書いていない段落の補完

未入力枠が一つでもあれば最終候補は生成できない。

## 7. PHASE 0〜8

- PHASE 0: 受領物を保全し、欠落と判読可否を記録する。
- PHASE 1: 要求、採点基準、AI規則、本人執筆契約を確定する。
- PHASE 2: 実験・分析計画を作り、G1へ進む。
- PHASE 3: 実験を実施し、生データと逸脱を封印する。
- PHASE 4: 分析を再生成可能にし、主要数値を追跡可能にする。
- PHASE 5: 出典を本文照合し、骨格PDFと文章枠を作り、G2へ進む。
- PHASE 6: 本人原文を受領・保全し、組版する。
- PHASE 7: 原文、意味、数値、引用、要求、採点基準を再監査する。
- PHASE 8: 全ページ目視、技術検査、教授視点評価を行い、G3後に固定する。

## 8. 主要ファイル

`spec/ASSIGNMENT_REQUIREMENTS.yaml`:
課題要求、採点基準、出典位置、重み、合格条件、教員提供か内部基準かを記録する。

`spec/ACADEMIC_INTEGRITY.yaml`:
AI利用規則、開示、本文本人執筆、意味変更の承認条件を記録する。

`spec/EXPERIMENT_PLAN.yaml`:
目的、変数、反復、順序、除外、停止条件、分析方法を事前登録する。

`spec/WRITING_PLAN.yaml`:
文章枠ID、表示名、節、目的、必須論点、予定する図表参照、証拠、採点基準、原文・組版ファイル、原文ハッシュ、意味変更状態を記録する。G2の承認値は骨格項目だけを固定し、本文受領で変わる状態・ハッシュ・校正メモは除外する。G3ではファイル全体を固定する。

`spec/SOURCES.yaml` と `SOURCE_AUDIT.md`:
発行主体、URL、言語、資料種別、確認箇所、対応主張、内容一致、採否理由を記録する。

`RESULT_TRACEABILITY.md`:
主要数値を生データ、処理、図表、本文へ接続する。

`quality/QUALITY_REVIEW.yaml`:
要求・採点基準への適合と、技術内容の内部QAを記録する。

`quality/PROFESSOR_REVIEW.yaml`:
採点基準別1〜5点、根拠、厳しい指摘、改善案、総合点、ready/reviseを機械検査可能に記録する。

`PROFESSOR_EVALUATION.md`:
同じ評価を本人が読める形でまとめる。実際の担当教員の採点ではない。

## 9. PDF生成モード

```powershell
python scripts/build_report.py experiments/<id> --mode skeleton
python scripts/build_report.py experiments/<id> --mode draft
python scripts/build_report.py experiments/<id> --mode candidate
```

- `skeleton`: PHASE 5後。本文ファイルが存在しても強制的に `（文章N）` を表示する。
- `draft`: G2後かつ全文章枠が完成したときの確認用。
- `candidate`: PHASE 7合格後の最終候補。G3承認前は提出版ではない。

G3承認後だけ次を実行する。

```powershell
python scripts/workflow.py release experiments/<id>
```

## 10. 標準様式

個別指定がない場合だけ次を使う。

- A4、1段組、本文10.5pt相当、上下左右25mm
- 本文明朝、見出しゴシック
- ページ番号のみ。ランニングヘッダなし
- 表紙の項目ブロックは中央配置
- 表紙後にタイトル、氏名、概要、キーワードを再掲しない
- 図表・コードは本文で先に番号参照する
- ページ上端・下端を基本とし、段落途中へ無理に固定しない
- 節境界を越えてフロートさせない
- 図キャプションは下、表とコードは上
- 一行キャプションは中央、複数行は読みやすい左寄せ
- 軸、凡例、表見出しは英語が必要な場合以外は日本語
- URLは黒、枠なし、本文系統の書体で折り返す
- 局所的な余白・字体変更は禁止し、授業指定の例外だけ `STYLE_OVERRIDES.yaml` に記録する

## 11. 出典の優先順位

1. 日本語の一次情報、公的機関、公式文書
2. 英語の一次情報、公式文書
3. 信頼できる日本語二次資料

検索結果の要約だけでは採用しない。実際の本文を開き、主張を直接支える箇所を特定する。適切な出典が不要な内容には、数を増やすためだけの参考文献を付けない。

## 12. 教授視点評価

完成候補に対し、G1で確定した全Rubric IDを評価する。各項目に次を必須とする。

- 1〜5点
- met / partially_met / not_met
- レポート内の具体的根拠
- 教授なら指摘する弱点
- 改善案

必須項目が `met` でなければ総合判定を `ready` にできず、G3準備を止める。模擬評価であり成績予測ではないことを常に明記する。

## 13. 最終成果物

- `report.pdf`: 提出用PDF
- `HANDOFF.md`: 作業、判断、結果、本人原文、未解決事項
- `PROFESSOR_EVALUATION.md`: 本人確認用の最終模擬評価
- `SOURCE_AUDIT.md`: 外部主張と確認箇所
- `RESULT_TRACEABILITY.md`: 数値と生データ・処理の対応
- `WORKLOG.md`: 時系列の作業・判断・相談・検証

通常、教員へ提出するのは `report.pdf` と授業指定物だけである。補助文書を一緒に提出するかは授業指示へ従う。

## 14. 診断とトラブル対応

```powershell
python scripts/doctor.py
```

この診断はPython依存、TeX、回帰テスト、完成例の再現性、承認状態、最終検査を確認する。

G1が通らない場合:
実習書の読了、採点基準の本人確認、表紙、AI規則、必須質問を確認する。

G2が通らない場合:
生データ封印、分析再現、出典検証、`WRITING_PLAN.yaml`、`build/skeleton.pdf` を確認する。

候補PDFが作れない場合:
全文章枠の `status: typeset`、原文ハッシュ、組版ファイル、意味変更状態、G2の有効性を確認する。

G3が通らない場合:
全ページ目視、`QUALITY_REVIEW.yaml`、`PROFESSOR_REVIEW.yaml`、必須基準の `met`、教授評価の `ready` を確認する。

## 15. 最小の実行例

```powershell
python scripts/doctor.py
python scripts/new_experiment.py sorting-2026 --title "ソートアルゴリズムの性能評価"
# Codexが資料を全読し、G1資料を作成
python scripts/workflow.py prepare-review experiments/sorting-2026 --gate G1
# 本人回答後
python scripts/workflow.py approve experiments/sorting-2026 --gate G1 --decision "承認 G1"
# 実験・分析・出典・骨格
python scripts/build_report.py experiments/sorting-2026 --mode skeleton
python scripts/workflow.py prepare-review experiments/sorting-2026 --gate G2
# 本人回答後、本人文章を受領・保存・組版
python scripts/build_report.py experiments/sorting-2026 --mode candidate
python scripts/render_pdf.py experiments/sorting-2026/build/final-candidate.pdf experiments/sorting-2026/quality/rendered --manifest experiments/sorting-2026/quality/RENDER_MANIFEST.yaml
# 品質監査と教授視点評価後
python scripts/workflow.py prepare-review experiments/sorting-2026 --gate G3
# 本人回答後
python scripts/workflow.py approve experiments/sorting-2026 --gate G3 --decision "承認 G3"
python scripts/workflow.py release experiments/sorting-2026
```

通常、これらのコマンドはCodexが実行し、ユーザーはG1〜G3と本文執筆に集中する。
