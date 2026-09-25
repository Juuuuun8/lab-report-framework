# lab-report-framework 詳細利用ガイド

## 1. このリポジトリの目的

このリポジトリは、大学の理工系実験レポートを「見た目のテンプレート」だけでなく、実習書の読解、事前確認、実験計画、実行、分析、出典検証、執筆、校正、最終検査まで一つの再現可能な流れとして管理するための環境である。

最優先するのは各授業の実習書、課題文、教員の明示指示である。共通様式は、個別指定がない箇所にだけ適用する。過去レポートの外観は規範にせず、情報処理学会の執筆作法と、日本の大学が公開する理工系レポート指針から授業レポートに適する部分を採用している。

この仕組みが守るものは次の4点である。

1. 根拠のない推測をしない。
2. 生データから本文の数値まで追跡できるようにする。
3. 外部主張は実際に出典本文を確認してから引用する。
4. PDFだけでなく、判断、出典、結果、作業履歴も引き渡す。

## 2. 作業ディレクトリ

CodexとAntigravityの作業ディレクトリには、必ずこのリポジトリのルートを指定する。

```text
lab-report-framework/          ← この階層を開く
├─ AGENTS.md
├─ ANTIGRAVITY.md
├─ README.md
├─ docs/
├─ rules/
├─ schemas/
├─ scripts/
├─ tex/
├─ templates/
├─ experiments/
└─ examples/
```

`experiments/<id>/` や `report/` を直接作業ディレクトリにすると、上位の役割分担、共通規則、検査スクリプト、TeXクラスを見落とすため使用しない。作業対象は会話または作業ログで `experiments/<id>/` と明示する。

## 3. 必要な環境

必須:

- Python 3.10以上
- PyYAML
- LuaLaTeX
- latexmk

検査とPDF画像化に使用:

- pypdf
- PyMuPDF

Python依存関係はリポジトリルートで次のように導入する。

```powershell
python -m pip install -r requirements.txt
```

TeX環境には、LuaLaTeX、LuaTeX-ja、Harano Ajiフォント、latexmk、および `tex/labreport.cls` が読み込むパッケージが必要である。WindowsではTeX Liveを想定しているが、コマンド名が同じなら他環境でもよい。

## 4. ルート直下のファイルと役割

### `AGENTS.md`

Codexの強制規約である。実習書の全読、質問、データ保全、出典検証、TeX作成、目視確認、Antigravity後の再監査を定める。Codexは作業開始時に必ず読む。

### `ANTIGRAVITY.md`

Antigravityの作業範囲を日本語推敲だけに制限する。数値、単位、式、図表、コード、引用番号、断定の強さ、TeXレイアウトは変更してはならない。変更後はCodexが再監査する。

### `README.md`

最短の導入手順と主要原則を示す入口である。詳細仕様は本書と `rules/` が担う。

### `requirements.txt`

Python側の依存パッケージを固定する入口である。

## 5. ディレクトリ構成

### `rules/`

人間とエージェントが読む規則である。

- `00-design-basis.md`: 参照した公式資料、採用・不採用の判断、独自決定。
- `10-layout-and-typography.md`: 用紙、余白、書体、表紙、文章。
- `20-figures-and-tables.md`: 図表の参照順、配置、キャプション、軸、罫線。
- `30-equations-and-code.md`: 数式、単位、コードリスト。
- `40-sources-and-citations.md`: 出典の優先順位、検証記録、参考文献。
- `50-evidence-and-writing.md`: 生データ、処理データ、結果、考察、追跡可能性。
- `60-deliverables.md`: 最終PDF以外に必要な成果物。
- `70-workflow-gates.md`: PHASE 0〜8の作業と合格条件。

### `schemas/`

YAMLファイルの期待構造をJSON Schemaで記述する。入力項目の定義書として使う。現行の `validate_experiment.py` は重要条件を直接検査しており、JSON Schema全体の自動検証はまだ行わない。

### `scripts/`

- `new_experiment.py`: 正規テンプレートを複製し、新しい実験を作る。
- `build_report.py`: 表紙YAMLから `meta.tex` を生成し、LuaLaTeXでPDF化し、成果物を集約する。
- `validate_experiment.py`: 指定Phaseまでの累積ゲートを検査する。
- `render_pdf.py`: PDF全ページをPNGへ変換し、目視確認を可能にする。

### `tex/`

`labreport.cls` を置く。全実験で共通の用紙、文字、見出し、表紙、キャプション、フロート、コード、参考文献の表示を定義する。

### `templates/experiment/`

新規実験の原型である。直接レポートを書く場所ではない。共通テンプレートを改善する場合だけ編集する。

### `experiments/`

実際の授業・実験ごとの作業場所である。1実験につき1ディレクトリを作る。

### `examples/sort-benchmark/`

架空データを使った完成見本である。レイアウト、追跡資料、検査フローを確認するためのもので、実測結果や提出用レポートではない。

## 6. 新しい実験の作成

リポジトリルートで実行する。

```powershell
python scripts/new_experiment.py sorting-2026 --title "ソートアルゴリズムの性能評価"
```

`experiment_id` は小文字英数字とハイフンだけを使用する。先頭は小文字英数字とする。同名ディレクトリが存在する場合は上書きせず停止する。

作成後の基本構成は次のとおりである。

```text
experiments/sorting-2026/
├─ instructions/
│  └─ INPUT_INVENTORY.md
├─ spec/
│  ├─ REPORT_META.yaml
│  ├─ USER_DECISIONS.yaml
│  ├─ EXPERIMENT_PLAN.yaml
│  └─ SOURCES.yaml
├─ data/
│  ├─ raw/
│  └─ processed/
├─ analysis/
├─ report/
│  ├─ main.tex
│  ├─ meta.tex
│  └─ sections/
├─ quality/
│  └─ FINAL_CHECK.yaml
├─ QUESTIONS.md
├─ HANDOFF.md
├─ SOURCE_AUDIT.md
├─ RESULT_TRACEABILITY.md
└─ WORKLOG.md
```

## 7. 実習書を受け取った直後に行うこと

1. 実習書、課題文、配布コード、データ、提出要件を `instructions/` または適切な入力場所へ保存する。
2. 元ファイルは変更しない。
3. ファイル名、種類、ページ数、ハッシュ、判読可否、用途を `instructions/INPUT_INVENTORY.md` に記録する。
4. 実習書を最初から最後まで読む。必要なページだけを拾い読みしてはならない。
5. 提出形式、必須章、実験条件、評価項目、禁止事項、指定表紙、期限を抽出する。
6. 不明点とユーザーが決める事項を `QUESTIONS.md` にまとめる。可能な限り実験前に一括して聞く。
7. 回答を `spec/USER_DECISIONS.yaml` に保存する。
8. PHASE 1が合格するまで実験を開始しない。

## 8. `REPORT_META.yaml`

表紙と文書の基本設定を持つ。

```yaml
cover:
  course_name: "情報工学実験"
  title: "実験題目"
  subtitle: "任意の副題"
  fields:
    - label: "所属"
      value: "情報理工学部 情報工学科"
    - label: "学生番号"
      value: "00000000"
    - label: "氏名"
      value: "山田 太郎"
    - label: "実験日"
      value: "2026年9月18日"
document:
  language: ja
  paper: A4
  columns: 1
  body_font_pt: 10.5
  punctuation: "，．"
```

`fields` は任意個数であり、所属、学年、班、共同実験者、担当教員、提出日などを授業ごとに追加・削除できる。固定項目ではない。項目一覧はラベル列と値列を一つのブロックとしてページ中央に配置し、値は読みやすい左揃えとする。

`report/meta.tex` はビルド時に自動生成されるため、直接編集しない。変更は必ず `REPORT_META.yaml` に行う。

## 9. `USER_DECISIONS.yaml`

実習書を全読した事実と、質問に対する決定を保存する。

- `instructions_read_complete`: 全読済みなら `true`。
- `instructions_read_at`: 読了日時。
- `questions`: `Q-001` 形式の質問一覧。
- `required_before_experiment`: 実験前に必須か。
- `status`: `open`、`resolved`、`delegated`。
- `decision`: 採用した回答。
- `decided_by`: `user` または `codex`。
- `decided_at`: 決定日時。
- `rationale`: 判断理由。

必須質問を `delegated` にするのは、ユーザーがCodexへ判断を明示的に委任した場合だけである。情報がないことを委任とみなしてはならない。

## 10. `EXPERIMENT_PLAN.yaml`

実験開始前に決める事項を保存する。

- `status`: 作成中は `draft`、承認後は `approved`。
- `objective`: 何を明らかにするか。
- `independent_variables`: 操作する変数。
- `dependent_variables`: 測定する変数。
- `controlled_variables`: 一定に保つ条件。
- `replications`: 本試行の反復回数。
- `warmups`: ウォームアップ回数。
- `random_seed`: 必要なら乱数種。
- `execution_order`: 条件の実行順序とランダム化方法。
- `exclusion_rules`: 除外条件。結果を見て後付けしない。
- `stop_conditions`: 安全、時間、異常に関する停止条件。
- `analysis`: 集計、統計、図表の作り方。
- `risks`: 実験上・解釈上のリスク。
- `safety_reviewed`: 安全確認済みなら `true`。

計画変更は上書きして終わらせず、変更理由と影響を `WORKLOG.md` に残す。

## 11. データと分析

### `data/raw/`

装置出力、ログ、観察記録などの未加工データを置く。一度記録した生データは上書きしない。再実験や再取得は別ファイルとして保存し、旧データとの関係をログへ記す。

### `data/processed/`

単位変換、整形、除外、集計前処理を行ったデータを置く。どの生データとどのスクリプトから生成したかを追跡可能にする。

### `analysis/`

処理、統計、表、図を再生成するコードを置く。手作業で数値を転記して二重管理しない。ソフトウェア版、乱数種、実行条件が結果に影響する場合は記録する。

失敗試行、欠測、外れ値、計画逸脱は隠さない。除外時は、事前規則または合理的な理由と影響を記録する。

## 12. レポートの標準様式

実習書の指定がない場合に次を適用する。

### ページ

- A4縦。
- 1段組。
- 上下左右25 mm。
- 表紙にページ番号を表示しない。
- 本文最初のページを1ページとする。
- ヘッダは置かない。
- フッタ中央にページ番号だけを置く。
- 原則として白黒でも意味が失われないようにする。

### 文字

- 本文: 10.5 pt相当、明朝体。
- 行送り: 約16.2 pt。
- 見出し: ゴシック体。節は本文より一段大きく太字。
- キャプション: 9 pt相当、明朝体、立体。
- コード: 等幅書体。
- URL: 本文と調和する書体、黒色、枠なし、自然な折返し。
- 本文字下げ: 1全角。
- 句読点: 標準は「，」「．」。実習書指定があれば従う。
- 文体: 「である」調を標準とし、混在させない。

### 表紙

- 上部に授業名。
- 中央付近に題目と任意の副題。
- 下部にユーザー指定項目のブロック。
- 項目ブロック全体の左右中央をページ中央に合わせる。
- 項目名は右揃え、値は左揃え。
- ロゴ、飾り枠、色面、概要、キーワードは標準では置かない。
- 表紙内容は `REPORT_META.yaml` だけから生成する。

### 本文開始

表紙の次はいきなり「1 目的」など実習書指定の最初の章へ入る。タイトル、氏名、所属、概要、キーワードを本文冒頭へ再掲しない。

章構成は実習書を優先する。指定がない場合は「目的」「原理または関連知識」「実験方法」「結果」「考察」「結論」「参考文献」を基本候補とするが、不要な章を形式のためだけに増やさない。

## 13. 図の規則

1. 本文で図の目的または読み取る点を述べ、「図 1」のように先に参照する。
2. 参照後の近傍へ置く。
3. ページ上端または下端へのフロートを基本にする。
4. 段落途中へ `[H]` で無理に固定しない。
5. キャプションは図の下に置く。
6. 軸に量と単位を書く。
7. 軸名、凡例、注記は英語が必要な場合を除き日本語にする。
8. 色だけに依存せず、線種とマーカーも変える。
9. 3D効果、濃い背景、不要な補助線を避ける。
10. 本文で主要傾向、比較、例外を説明する。

TeXでは原則として `[tbp]` を使う。参照したページに収まらない場合は、次ページ上端が自然な配置である。

## 14. 表の規則

1. 本文で先に「表 1」を参照する。
2. キャプションは表の上に置く。
3. 見出しは日本語を基本とする。
4. 量と単位を明示する。
5. 縦罫線を使わず、必要最小限の横罫線にする。
6. 桁数、有効数字、単位を揃える。
7. 分析出力から生成し、本文との二重管理を避ける。
8. 長い表は付録または複数ページ表とし、見出しを繰り返す。

## 15. コードリストの規則

- 本文で先に「リスト 1」を参照する。
- キャプションはコードの上に置く。
- 議論に必要な最小部分だけを載せる。
- 等幅書体、行番号、控えめな枠と背景を使う。
- 長い完全版は別ファイルまたは付録に置く。
- 抜粋や省略は明記する。
- 端末出力はスクリーンショットではなくテキストを使う。
- APIキー、認証情報、個人情報、端末固有の絶対パスを載せない。

## 16. 数式と単位

- 数式も文章の一部として扱い、必要なら句読点を付ける。
- 本文で参照する式だけに番号を付ける。
- 本文では「式 (1)」のように参照する。
- 使用する記号は式の前後で定義する。
- 変数は斜体、演算子、単位、関数名は立体とする。
- 数値と単位を分離し、SI単位系を基本とする。
- 有効数字は測定精度と処理方法に合わせる。
- 長い導出が本文の論理を分断する場合は付録へ移す。

## 17. 結果と考察

結果節には、測定・観察した事実と数値を書く。原因の推測、評価、感想を混ぜない。

考察節では、次を区別して書く。

- 観測事実
- 出典で確認した既知の理論
- それらから導く推論
- 代替説明
- 誤差要因と限界
- 結果を適用できる範囲

「理論どおりだった」だけで終わらせず、差、比、傾向、不確かさを定量的に示す。ただし少数点から一般法則を証明したように断定しない。

## 18. 参考文献の探索順位

1. 日本語の一次情報、公的機関、標準化団体、大学、学会、公式ドキュメント。
2. 英語の一次情報、標準、原著論文、公式ドキュメント。
3. 専門家、大学、出版社などによる信頼できる日本語二次資料。
4. その他の二次資料は、上位資料がなく、著者、根拠、更新日を評価できる場合だけ。

日本語であることだけを理由に個人ブログを英語一次情報より優先してはならない。検索結果の要約、AI要約、ページタイトルだけで採用してはならない。

## 19. `SOURCES.yaml` と出典検証

各出典に `S-001` 形式のIDを付ける。

- `language`: `ja` または `en`。
- `source_class`: `primary_official`、`primary_research`、`secondary_reliable`。
- `organization`: 発行主体。
- `title`: ページまたは文献の題名。
- `url`: 直接URL。
- `published_or_updated_at`: 分かる場合の公開・更新日。
- `accessed_at`: 実際に確認した日。
- `verification.status`: 採用時は `verified`。
- `locator`: 節、見出し、ページ、段落など確認位置。
- `supports_claims`: `C-001` 形式の主張ID。
- `match_note`: なぜその箇所が主張を支えるか。
- `selection_note`: 採用理由と上位資料の探索結果。

同じ情報を人間が一覧しやすい形で `SOURCE_AUDIT.md` にもまとめる。本文の参考文献は初出順とし、Web資料には発行主体、題名、URL、分かれば公開・更新日、アクセス日を記す。

## 20. 結果の追跡可能性

`RESULT_TRACEABILITY.md` では、各主要結果を `R-001` 形式で管理し、次を結び付ける。

- 生データ
- 処理済みデータ
- 分析スクリプトと版
- 集計式または処理方法
- 出力された表・図
- 本文の節と記述
- 検算またはレビュー結果

本文の数値を手で書き換えた場合は追跡が切れる。可能な限り分析結果から表や図を生成し、本文数値も同じ出力と照合する。

## 21. PHASE 0〜8

検査は累積である。たとえば `--phase 6` はPHASE 0から6までをまとめて確認する。

### PHASE 0: 受領・保全

入力一覧を作り、欠落、破損、判読不能を確認する。元ファイルを変更しない。`INPUT_INVENTORY.md` が空またはプレースホルダを含むと不合格になる。

### PHASE 1: 要求理解・事前質問

実習書を全読し、質問へ回答を得る。`instructions_read_complete: true`、読了日時、必須質問の解決または明示委任、表紙情報が必要である。標準設定はA4・1段・10.5 ptである。

### PHASE 2: 実験計画

計画を `approved` にし、目的、変数、反復、実行順、除外規則、停止条件、分析方法、安全確認を確定する。

### PHASE 3: 実験実行

`data/raw/` に実データを保存し、`WORKLOG.md` にPHASE 3の記録を残す。

### PHASE 4: 分析

`data/processed/`、`analysis/`、完成した `RESULT_TRACEABILITY.md` が必要である。

### PHASE 5: 出典検証

各出典が `verified` で、発行主体、題名、URL、アクセス日、言語、種別、確認位置、対応主張、一致説明、採用理由を持つことを確認する。

### PHASE 6: 執筆・TeX

`labreport` クラスの使用、禁止構造の不使用、プレースホルダ解消、図表のキャプションとラベル、本文先行参照、図下・表上・リスト上キャプション、`HANDOFF.md` を検査する。`[H]` は記録された例外がない限り禁止である。

### PHASE 7: 日本語推敲・再監査

Antigravityの推敲後にCodexが技術内容を再監査し、`WORKLOG.md` に `Codex再監査: 完了` を記録する。

### PHASE 8: 提出物固定

PDFと4つの補助成果物を `deliverables/` に集約する。目視・技術検査を `FINAL_CHECK.yaml` で `passed` にし、PDFが表紙と本文を持つA4文書であることを検査する。

各段階の実行例:

```powershell
python scripts/validate_experiment.py experiments/sorting-2026 --phase 0
python scripts/validate_experiment.py experiments/sorting-2026 --phase 1
python scripts/validate_experiment.py experiments/sorting-2026 --phase 2
```

失敗時は表示された項目を修正し、同じPhaseを再実行する。検査を無効化して先へ進めない。

## 22. TeX原稿の構成

`report/main.tex` はクラス、表紙メタデータ、各節を読み込む入口である。本文は `report/sections/` に分ける。ファイル名の番号は読み込み順を分かりやすくするためのもので、章構成は実習書に合わせて変更できる。

ラベルは種類が分かる接頭辞を使う。

- 図: `fig:`
- 表: `tab:`
- 式: `eq:`
- コード: `lst:`

本文で `\ref` または `\eqref` を使い、表示番号を手入力しない。

## 23. PDFのビルド

```powershell
python scripts/build_report.py experiments/sorting-2026
```

この処理は次を行う。

1. `REPORT_META.yaml` を読み、TeX特殊文字をエスケープする。
2. `report/meta.tex` を再生成する。
3. 実験固有の `build/tex-cache/` を使用する。
4. `latexmk -lualatex` で `build/main.pdf` を作る。
5. PDFを `deliverables/report.pdf` へコピーする。
6. 4つの補助成果物を `deliverables/` へコピーする。

`report/meta.tex` と `build/` は生成物である。表紙修正はYAML、本文修正は節ファイル、様式修正は `tex/labreport.cls` に行う。

## 24. 全ページの目視確認

```powershell
python scripts/render_pdf.py `
  experiments/sorting-2026/deliverables/report.pdf `
  experiments/sorting-2026/quality/rendered `
  --dpi 160
```

全ページで次を確認する。

- 文字欠け、豆腐、重なり、はみ出しがない。
- 表紙の題目と項目ブロックが意図どおり中央にある。
- 本文が1ページから始まる。
- 見出しだけがページ末に孤立していない。
- 図表が本文の初回参照より前に出ていない。
- 図は下、表とリストは上にキャプションがある。
- 軸、凡例、単位、表見出しが読める。
- URLが余白を越えず、参考文献が判読できる。
- 不自然な大空白や段落分断がない。

修正したらPDFを再生成し、変更ページだけでなく全ページを再確認する。結果を `quality/FINAL_CHECK.yaml` と `WORKLOG.md` に記録する。

## 25. 必須成果物

`deliverables/` には最低限次を揃える。

- `report.pdf`: 提出用レポート。
- `HANDOFF.md`: 作業内容、意識した点、結果、本文への反映、未解決事項、再生成方法、提出物一覧。
- `SOURCE_AUDIT.md`: 本文主張と出典の対応、確認位置、内容一致、採否理由。
- `RESULT_TRACEABILITY.md`: 数値、図表、結論とデータ・処理の対応。
- `WORKLOG.md`: 日時、担当、Phase、入力、実行、判断根拠、変更、異常、相談、検証。

必要に応じて分析コード、処理済みデータ、環境情報、検査ログも含める。ただし認証情報や不要な個人情報は入れない。

## 26. CodexとAntigravityの分担

Codexが担当する:

- 実習書読解と質問
- 実験計画、実行、分析
- 出典検証
- 数値、式、図表、コード
- TeXとPDF
- 技術監査と最終判断

Antigravityが担当できる:

- 誤字脱字
- 助詞と主語述語
- 「である」調
- 冗長表現
- 曖昧な指示語
- 語順と段落接続
- 用語表記の統一

Antigravityは内容を追加せず、疑問は修正ではなく `QUESTIONS.md` への提案とする。Codexは返却差分を確認し、数値、単位、式、引用、断定の強さが変わっていないことを再監査する。

## 27. 実習書と共通規則が衝突した場合

実習書を優先する。次の手順を取る。

1. 衝突箇所を特定する。
2. 実習書の該当ページまたは節を記録する。
3. 必要ならユーザーへ確認する。
4. 採用した判断を `USER_DECISIONS.yaml` に保存する。
5. 共通規則から外れた理由と影響を `WORKLOG.md` に残す。
6. 自動検査と衝突する場合は、検査を黙って削除せず、例外を明示的に実装・記録する。

## 28. 自動検査だけでは判定できない事項

自動検査は存在、形式、一部の参照順、A4寸法を確認できるが、次は人間またはCodexの意味上の確認が必要である。

- 実習書を本当に全ページ読んだか。
- 出典の本文が主張を正しく支えているか。
- 結果と考察が混ざっていないか。
- グラフが誤解を招かないか。
- 有効数字と不確かさが適切か。
- 考察の因果関係がデータ以上に強くないか。
- PDFの視覚的な重心、読みやすさ、余白が適切か。

このため、`validate_experiment.py` の成功だけで完成とはしない。PHASE 8の目視記録が必要である。

## 29. よくある問題

### 表紙を直したのにPDFが変わらない

`report/meta.tex` ではなく `spec/REPORT_META.yaml` を直し、`build_report.py` を再実行する。

### 図表が意図した位置に来ない

本文の参照位置を先に確認する。段落中へ固定せず `[tbp]` を使い、次ページ上端を許容する。大きすぎる場合は縮小、分割、単独ページ、付録を検討する。

### PHASE 1が通らない

`instructions_read_complete`、読了日時、必須質問の状態と回答、表紙の未確定値を確認する。

### PHASE 6が通らない

プレースホルダ、`\maketitle`、abstract、2段組、`[H]`、キャプションやラベルの欠落、本文先行参照を確認する。

### PHASE 8が通らない

`deliverables/` の5ファイル、`FINAL_CHECK.yaml` の2つの `passed`、PDFのA4寸法を確認する。補助文書を更新した後は再ビルドして `deliverables/` へコピーし直す。

### TeXの警告が出る

未解決参照、Overfull/Underfull、重複リンク先、フォント欠落を優先して解消する。環境依存の情報警告は内容と出力を確認し、問題がない根拠を最終記録へ残す。

## 30. 標準の完了手順

```powershell
# 1. 新規実験
python scripts/new_experiment.py sorting-2026 --title "実験題目"

# 2. 実習書全読、質問、回答保存後
python scripts/validate_experiment.py experiments/sorting-2026 --phase 1

# 3. 計画承認後
python scripts/validate_experiment.py experiments/sorting-2026 --phase 2

# 4. 実験、分析、出典検証、執筆を各ゲートで確認
python scripts/validate_experiment.py experiments/sorting-2026 --phase 7

# 5. PDF生成
python scripts/build_report.py experiments/sorting-2026

# 6. 全ページ画像化と目視確認
python scripts/render_pdf.py experiments/sorting-2026/deliverables/report.pdf experiments/sorting-2026/quality/rendered --dpi 160

# 7. FINAL_CHECKとWORKLOGを更新後に最終検査
python scripts/build_report.py experiments/sorting-2026
python scripts/validate_experiment.py experiments/sorting-2026 --phase 8
```

最終的に、PDFを見ただけでなく、ユーザーが `HANDOFF.md` から作業全体を理解でき、`SOURCE_AUDIT.md` から引用根拠を確認でき、`RESULT_TRACEABILITY.md` から数値を生データへたどれ、`WORKLOG.md` から判断経緯を復元できる状態を完成とする。
