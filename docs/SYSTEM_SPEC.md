# 現在のシステム概要・詳細仕様（v7.2）

2026-10-03時点のPython、TeXクラス、JSONスキーマ、テンプレート、CI設定から整理した実装仕様。過去の会話や旧版の説明を実装済みの証拠にはしていない。運用指示によってAI・本人が行う判断と、プログラムが検査する事項を区別する。

全データ項目・必須性・列挙値・型・正規表現・個数制限は [スキーマ全項目](SCHEMA_REFERENCE.md) に掲載する。この文書はそれに加えて処理順、条件、例外、保存先、制限を説明する。

## 1. 何であり、何ではないか

これはローカルのレポート作業用テンプレート、手順、検査・生成コマンドの集合である。常駐サーバー、GUI、AI API呼出し、プロンプト自動実行器は実装されていない。Codexが実習書・データを読み、必要なファイルを編集し、Pythonコマンドを実行する。Python自身は解法を考えたり、誤字を直したり、Webを読んだり、教授として採点したりしない。

本人が本文を書き、AIが実験支援・分析・骨格・校正・組版・監査を行うことはAGENTSと運用規則の契約である。Pythonは、その契約に対応した記録・ファイル・ハッシュ・状態を検査する。記録の真実性、本人の理解、実際の成績を機械だけで証明する仕組みではない。

## 2. 構成と依存関係

作業ルートはリポジトリ直下。実験ごとに `experiments/<id>/` を作る。

| 場所 | 役割 |
|---|---|
| AGENTS.md / rules/ | AIに対する運用指示。Pythonから自動実行されない |
| config/system-version.yaml | システム・互換形式の版情報 |
| config/style-contract.yaml | 共通TeXクラスの正規化ハッシュと様式契約 |
| schemas/ | 19件のJSON Schema。構造・型・必須項目を定義 |
| scripts/ | 検査、承認記録、受領、再現、PDF、表示資料の処理 |
| templates/experiment/ | 新規実験の雛形。未決事項はTODO等のまま |
| tex/labreport.cls | 共通の日本語レポート様式 |
| examples/sort-benchmark/ | 架空の完成例。実測資料として使わない |
| tests/ | 正常系・拒否条件・新規テンプレートからの通し試験 |
| docs/ | 説明書。日々の処理に全読は不要 |

実験内は `instructions/`（配布資料）、`spec/`（確定条件・対応表）、`data/raw/`（生データ）、`data/processed/`（処理結果）、`analysis/`（分析）、`report/`（骨格TeX）、`prose/original/`（原文）、`prose/typeset/`（組版）、`prose/history/`（旧版）、`quality/`（確認・生成記録）、`workflow/`（承認）、`build/`（一時生成物）、`deliverables/`（固定版）を使う。一部の空ディレクトリは必要時に処理側が作る。

Python 3.10以上をdoctorが要求する。依存はPyYAML >=6,<7、jsonschema >=4,<5、pypdf >=5,<7、PyMuPDF >=1.24,<2。PDF生成はローカルのlatexmkとLuaLaTeXを使う。TeXクラスはltjsarticle、luatexja、原ノ味プリセット、geometry、caption、listings等を読み込む。実験固有のグラフ用ライブラリ等は別途必要となり得る。

## 3. 三つの承認と内部検査段階

```text
要件・計画 → G1 → 実験・分析・出典・骨格 → G2
→ 本人原文 → 校正・組版・完成候補・監査 → G3 → 提出版固定
```

PHASEは0〜8の累積検査である。指定した段階以前も検査する。段階ごとにユーザー承認を9回取る構造ではない。

| 段階 | 実装上の主要検査 |
|---|---|
| 0 | INPUT_INVENTORYが空でなく、未記入表現がない |
| 1 | QUESTIONS、USER_DECISIONS、表紙、実習書読了記録、要求、採点基準、AI利用条件、CONTEXT_INDEX、STATE。新形式の課題範囲 |
| 2 | 実験計画のapproved、安全確認、目的・変数・回数・除外・停止・分析等の記録 |
| 3 | 有効なG1、生データと実行記録のハッシュ・サイズ、封印日時、WORKLOGのPHASE 3、実施事実・データ確認 |
| 4 | 処理済みデータと分析コード、R-IDを含む結果追跡表、期待出力の封印値との一致 |
| 5 | 出典・主張の検証記録とID対応、出典表、文章枠・予定参照・採点対応・TASK対応、骨格範囲レビュー、様式・TeX。--skeleton時はPDFと枠も検査 |
| 6 | 有効なG2、本人原文と組版・レビューの版、意味変更状態、実参照。--draft時は未完成枠を許す |
| 7 | WORKLOGの本人原文保全・意味変更・Codex再監査の完了記録 |
| 8 | 成果物、技術・内容・教授評価、TASK最終レビュー、確認対象のPDF版、画像記録、PDF条件。提出版検査ではG3と固定文書の一致も検査 |

実習書の読了、実施事実、範囲準拠、コメントの妥当性は記録値と判断根拠を検査している。実際に読んだか、実験したか、意味が適切かを検査器が認識するわけではない。

## 4. 課題別の学習範囲（今回追加）

`ASSIGNMENT_REQUIREMENTS.yaml.task_scopes` に次を課題順に記す。

| 項目 | 内容 |
|---|---|
| task_id / title | TASK-001形式の識別子と課題名 |
| instruction_scope | 当該課題までの実習書の節・ページ、既習範囲の出典 |
| prior_task_ids | 前提課題。配列内で先に宣言されたTASKだけを許す |
| allowed_knowledge | 使用する知識・手法・ライブラリ。1件以上 |
| excluded_knowledge | 持ち込まない後続内容・手法。追加指定がなければ空配列可 |
| requirement_ids | 既存requirementsの指定条件を参照。1件以上 |
| submission_code | 提出コードの実験相対パス。コード提出なしなら空配列 |
| helper_code | 検算・集計等の補助コードの相対パス。なければ空配列 |
| comment_policy | コメントの言語・指定・説明すべき内容 |

PythonはTASK重複、未知・後続・自身への前提参照、未知REQ、未決内容、実験外パス、提出と補助の同一ファイル、PHASE 5以降の宣言コード欠落を拒否する。言語ごとのimport解析、AST解析、後続課題の解法検出、コメントの意味判定は実装していない。未登録コードを網羅的に発見する機能でもない。

文章枠には `task_ids` を付ける。複数課題に共通の文章は複数指定可。全枠が既知TASKに対応し、全TASKがいずれかの枠に含まれる必要がある。

骨格は `WRITING_PLAN.yaml.task_scope_reviews`、最終は `PROFESSOR_REVIEW.yaml.task_scope_reviews` に記録する。各TASKにつき1件だけ、`task_id`、`status`、`evidence` を持つ。statusはpassed/failed/pending。通過には全件passedと空でない未記入表現を含まない根拠が必要。根拠の教育的妥当性はAI・本人が判断する。

G1確認票には範囲と指定を表示する。G2では執筆案内に反映する。G3では教授評価文書に最終確認を表示する。宣言したコードはanalysisやreportの外にあってもG2のハッシュ対象となる。G1の範囲変更は後続承認も失効させる。

新規STATEはversion 2で範囲宣言が必須。version 1の旧実験で未設定なら従来検査を維持し、「学習範囲監査は未適用」と表示する。既存の架空完成例はこの旧形式である。未適用のまま範囲準拠を確認済みとは扱わない。新たに適用する際は範囲・枠・レビューを追加し、version 2へ更新してG1から必要な再承認を行う。自動移行は実装していない。

## 5. 指示・要件・計画のデータ

- `USER_DECISIONS.yaml`: 読了日時、質問、実験前必須か、未解決/解決/委任等、回答を記録する。実験前必須質問はresolved/delegatedとdecisionが必要。
- `ASSIGNMENT_REQUIREMENTS.yaml`: 科目・題目・提出形式・期限、資料のパス/任意ハッシュ/読了/範囲、REQ-IDの要求と禁止、教員基準か内部基準か、RUB-IDの評価基準・合格条件・任意配点、TASK範囲。
- `ACADEMIC_INTEGRITY.yaml`: 利用規則、AI許可/禁止範囲、本文本人執筆契約、開示、実施事実・データ・出典・説明可能性の確認。
- `EXPERIMENT_PLAN.yaml`: 目的、独立/従属/統制変数、反復、順序、除外、停止、分析、安全。warmups/random_seed/risksは任意。
- `CONTEXT_INDEX.yaml`: 資料パス、ハッシュ、確認済み要約等。再開時の参照用。

plan.statusのapprovedとG1の本人承認は別の記録である。計画ファイルをapprovedにしてもG1承認がなければPHASE 3へ進めない。

## 6. 実験・再現性・出典

`EXECUTION_MANIFEST.yaml` は試行の環境・版・日時・状態・条件・生データ一覧等を記録する。`workflow.py seal-data` は現在の生データの生バイトSHA-256とサイズを記録する。後の検査はそれに一致するかを見る。実測か捏造かの判定、改変不能ストレージ、電子署名はない。

`REPRODUCE.yaml` は実行コマンドargv、作業ディレクトリ、期待出力、封印値を持つ。`{python}` は実行中のPythonへ展開する。sealは現在の出力を記録し、verifyは現在値を照合してから実験を一時コピーし、期待出力を取り除いてコマンドを実行し、再生成物を照合する。生成対象にraw配下や.pyを指定することは拒否する。許容誤差比較ではなく、テキスト改行正規化後のハッシュ・サイズ一致である。

再現コマンドは通常のsubprocessで実行され、専用サンドボックスやネットワーク隔離、時間制限は実装されていない。実験側の任意コマンドを、確認なしに安全と扱ってはいけない。

`RESULT_TRACEABILITY.md` はR-001等で生データ、処理、図表、主張を結ぶ正本。検査器はR-IDの存在や他記録との対応を見るが、表中の数式を意味理解して検算するわけではない。

`SOURCES.yaml` はS-ID、言語ja/en、一次公式/一次研究/信頼できる二次資料、発行主体、題名、URL、アクセス日、確認位置、対応C-ID、内容一致と選定理由を持つ。`CLAIMS.yaml` は外部主張/結果/推論/限界/方法を区別し、本文位置と出典・結果IDを結ぶ。

PHASE 5では登録された出典・主張を全てverifiedにする必要がある。外部主張に出典、結果にResult ID、推論に少なくとも出典または結果が必要。未知IDは拒否する。スキーマ上candidate/rejected/draft等が許されても、そのままG2へは進めない。

サイト本文の取得や一致判定、日本語一次情報の探索はAIが行う運用であり、PythonにはWeb取得処理がない。検証済みという記録だけで出典内容の正しさを証明してはいない。

## 7. 骨格と本人原文

WRITING_PLANはplanning/skeleton_ready/prose_partial/prose_completeを持つ。各P-001形式の枠には文章N、節、目的、必須論点、予定参照、証拠ID、採点ID、TASK、執筆者、状態、原文/組版パス、原文ハッシュ、意味変更、確認メモと版付きレビューを記す。student_judgmentは任意の考察の問い。

雛形は目的・実験方法・結果・考察・結論の5枠。課題に合わせて追加・変更する。TeXの `\proseslot{P-001}{文章1}` と枠のID・表示・数が対応する必要がある。骨格は全枠を囲み付きの（文章N）として表示する。

本人から受領した本文は `receive_prose.py` にバッチで渡す。バッチは `receipt`（受領元の説明）、`paragraphs`（slot_id/textの配列）。空配列、空本文、未知・重複枠、不正なパス、封印済み原文の改変、G1/G2未承認を拒否する。本文を自動生成・校正する処理ではない。

変更前の対応表・原文・組版を履歴へ保存し、新原文を保存する。旧組版を退避し、状態をuser_submitted、全体をprose_partialにする。旧レビューを削除する。同文の再送は変更しない。例外時は変更対象と差分文書を復元するが、OS停止中の完全なトランザクション保証や多重実行ロックはない。

校正・TeX化はAIの編集作業である。`review_prose.py --slot ... --note ...` は実際の読み比べ後に記録する。数値・単位が違う場合は `--decision "承認 P-001: 具体的な変更"` が必要。原文・組版ハッシュ、判定、判断文、メモ、日時を保存する。原文が既存の受領ハッシュと違う場合は勝手に再封印しない。

数値検査はNFKC、参照表記除外、桁区切り処理後の数値列と指定単位列の順序比較。単位はms/ns/s/mm/cm/m/kg/g/Hz/kHz/MHz/V/A/W/Pa/K/mol/%。単位換算や式の数学的同値を解かず、否定・因果・断定の変化も自動判定しない。Decimal正規化のため1.0と1.00の有効数字差はこの数値比較では区別しない。有効数字は別途確認する。

`PROSE_DIFF.md` は原文とTeXの詳細差分。`PROSE_CHANGES.md` は確認メモから日本語の変更案内を生成する。機械が意味差分を要約したものではなく、メモの適切さはAIの責任である。レビューが古ければ旧メモと表示し、組版待ちならその状態を示す。

## 8. PDF生成の実処理

`build_report.py` はREPORT_METAからmeta.texを生成してから累積検査を行う。skeletonはPHASE 5、draftはPHASE 6 --draft、candidateはPHASE 7。検査成功後にbuild/report-mode.texを書き、latexmk -lualatex -g -interaction=nonstopmode -halt-on-error -recorderを実行する。毎回TeXを再実行する。

フォントキャッシュはbuild/tex-cache、TEXINPUTSには共通texディレクトリを追加する。標準出力はbuild/latexmk-output.logへ保存し、失敗時は末尾25行を表示する。未解決参照・引用、ラベル重複、Overfull hbox/vboxが検出されたら失敗とする。

| モード | 出力 | 本文 |
|---|---|---|
| skeleton | build/skeleton.pdf | 全枠を文章Nにする |
| draft（既定） | build/draft.pdf | 確認済み枠を反映。未完成枠は残す |
| candidate | build/final-candidate.pdf | 全枠の完成を要求 |

未確認のtypesetファイルが存在する枠はdraftでも拒否する。candidate作成だけでは最終監査・G3・提出固定を完了しない。HANDOFF完成はPHASE 8で要求し、初回候補作成前には要求しない。

## 9. 組版の具体値

以下は `tex/labreport.cls` の実設定であり、全大学共通の規格を意味しない。

| 項目 | 実設定 |
|---|---|
| 基底クラス | ltjsarticle、a4paper/10pt/oneside |
| 本文 | 文書開始時に10.5pt、行送り16.2pt |
| 余白 | 上下左右25mm |
| 字下げ・段落間 | 1zw、0pt |
| 日本語字体 | luatexjaのharanoajiプリセット。本文は明朝、見出しはsffamily |
| ページ番号 | 表紙なし、本文からアラビア数字。フッタ中央のみ |
| 見出し | section: large・ゴシック太字、subsection: normalsize・ゴシック太字、subsubsection: normalsize・ゴシック |
| 見出し前後 | section 2.0/0.7、subsection 1.5/0.5、subsubsection 1.2/0.4 baselineskip |
| キャプション | small/roman、ラベル通常体、区切りquad、justified、singlelinecheck=true、skip 6pt |
| キャプション位置 | 図下、表上、リスト上。キャプションのpt値を直接9pt固定してはいない |
| フロート割合 | 上0.88、下0.75、本文最小0.10、フロートページ0.75 |
| フロート数 | 上3、下2、合計4 |
| フロート間隔 | 本文間14pt +4/-3、相互12pt +3/-2、文中14pt +4/-3 |
| 配置補助 | flafterで参照以前への配置を抑制、placeinsのsection境界 |
| コード | small等幅、左行番号scriptsize、番号間0.8em、自動折返し、空白保持、上キャプション |
| コード枠 | single、線0.3pt・black!35、背景black!2。完全な枠なしではない |
| コード前後 | 1.0/0.8 baselineskip |
| URL | urlstyle same、hidelinks、リンク枠なし、xurlで折返し |
| 文献 | 参考文献の無番号節、[連番]、項目間0.35 baselineskip、parsep 0pt |
| 引用マクロ | sourceciteの引数を上付き角括弧で表示。自動書誌取得ではない |

表紙は授業名largeゴシック、題目22pt/31ptゴシック太字、任意副題large。上空白18mm、授業名後24mm、副題前5mm、下16mm。項目表は全体を中央へ置き、ラベル右揃え・値左揃え、列間1.5em、行追加間隔0.65em。各値自体を中央揃えにする方式ではない。

標準テンプレートは表紙後すぐ本文に入り、表紙情報の再掲・概要・キーワードを置かない。検査はtwocolumn、abstract、maketitle、author等を拒否する。図表とリストのcaption/labelと先行ref、検出可能なキャプション上下を検査する。任意マクロや全TeX構文を解釈するわけではない。

数式の記号定義、変数/単位の字体、句読点、軸・凡例の日本語、文章の自然さは主に運用・目視確認事項である。

## 10. 軽微調整と様式変更

任意の `spec/LAYOUT_TUNING.yaml` は専用Python検査で、figure_width 0.6〜1.0（既定0.82）、textfloatsep_pt 10〜20（既定14）、floatsep_pt 8〜18（既定12）だけを許す。bool、非数値、非有限値、未知キーを拒否する。

図はG2前から `width=\ReportFigureWidth` を使う。固定幅の図には効果がない。骨格では既定値、draft/candidateでは設定値を使う。設定ファイルがなければ従来の伸縮間隔を維持し、ある場合の指定間隔は固定ptにする。G2を取り直さず、候補再生成とG3目視へ回せる。

`STYLE_OVERRIDES.yaml` は設定名、値、理由、出典、承認者、日時を記録する。検査器は該当するTeXコマンド名の使用許可を確認するが、valueを自動でTeXへ適用する機能はない。A4・1段組・10.5ptの検査は別途固定されているため、別用紙・別段組をYAMLだけで自由に切り替えることはできない。授業の指定が標準と異なる場合は実装側も含めて対応を判断する。

共通クラスの変更はstyle-contractのハッシュ不一致として検出される。照合値更新自体が目視確認を実施するわけではない。

## 11. 承認・版管理

STATEには全体のcurrent_gate/statusとG1/G2/G3の状態、準備日時、決定日時・主体・原文、対象ダイジェスト、ファイル一覧、確認票パスを保存する。新規はversion 2、current_gate G1、status preparing、各gate pending。

prepare-reviewは前段承認を確認し、G1はPHASE 2、G2はPHASE 5 --skeletonと分析再現、G3はPHASE 8 --candidateを実行する。成功後、確認票を作りawaiting_userにする。要約は5項目で、別途確認事項と変更ファイル・課題別範囲を示す。

approveはawaiting_userで対象が変わっていないこと、前段承認、decisionが「承認 G1」等で始まることを確認する。G1/G2の後は次のgate/executing、G3の後はcomplete/approved。release後にcomplete/releasedとなる。staleは保存状態の列挙値ではなく、再計算時の判定である。

本人のチャットを自動購読して認証する機能はない。decisionを渡す操作主体が本人回答を正しく転記する前提である。暗号署名・改竄耐性のある承認サービスではない。

| 承認 | 対象の概要 |
|---|---|
| G1 | instructions、QUESTIONS、USER_DECISIONS、REPORT_META、要求/TASK、AI規則の事前契約、実験計画、索引、様式例外 |
| G2 | 実行記録、再現設定、出典・主張、raw/processed/analysis、結果表・出典表、WRITING_PLANの構造とTASKレビュー、report、骨格生成記録、宣言コード、実施事実・データ確認、上流G1 |
| G3 | report、prose（履歴含む）、WRITING_PLAN全体、最終補助文書、品質・教授・画像・候補生成記録、本文差分、AI事後確認、LAYOUT_TUNING、候補PDF、上流G1/G2 |

テキストmd/tex/yaml/yml/json/csv/txt/dat/pyは改行を正規化してSHA-256を計算する。サイズは記録するが承認ダイジェストから除く。キャッシュや.gitkeep等は通常対象外。G2の原文受領状態・ハッシュ・校正メモは構造から除くため、本文を書くたびにG2は失効しない。

生成記録はversion=1、mode、inputs_digest、inputs（path/sha256/bytes）、dependencies、pdf_sha256を持つ。入力はreport/processed/analysis/表紙/様式/文章構造/共通tex/様式契約。draft/candidateはproseとLAYOUT_TUNINGも含む。TeX recorderが読む実験内の追加入力も加える。保存された入力一覧と現在入力の両方を照合する。

G2の骨格PDFはbuildになければpreviewを使い、それもなければ生成入力記録だけを照合する。G3の候補PDFはbuildになければdeliverables/report.pdfを使う。提出固定そのものにはbuild/final-candidate.pdfが必要である。

## 12. 最終監査と教授評価

`FINAL_CHECK.yaml` は目視・技術状態等、`QUALITY_REVIEW.yaml` は採点対応と8個の内容チェック、`PROFESSOR_REVIEW.yaml` は基準別評価とTASK最終確認を持つ。

内容チェックはrequirements_coverage、technical_accuracy、quantitative_consistency、argument_quality、limitations、source_quality、academic_integrity、oral_defense。全てpassedと根拠が必要。必須REQ-IDの記載も検査する。

教授評価は確定した全RUB-IDと一致する必要があり、必須基準はmet、総合はreadyが必要。任意基準の不十分さは残せるが、総合判断や技術チェック、TASK確認は別途通過する必要がある。TASKは全件passed。判定はAIが行うもので、Pythonの自動採点ではない。

教員提供基準で全項目に正のmax_scoreとweightがある場合だけ得点を認める。各scoreを0〜max_scoreに制限し、総合値は `round(100 * Σ(score/max_score * weight) / Σweight, 2)` と0.005未満の差で一致する必要がある。条件が揃わなければ得点・総合点はnull。

PDFは2ページ以上、各ページA4（縦横とも1mm未満の差）、抽出可能文字あり、検出対象フォントの埋込み、空でないURI、文章Nの残存なしを検査する。リンク先への通信確認やアクセシビリティ規格の完全検証はない。

`render_pdf.py` は既定150dpiで全ページをPNG化し、PDFハッシュ、日時、dpi、枚数、画像の相対パス/ハッシュ/サイズを記録する。manifest指定時は出力先をその親ディレクトリ内へ制限する。PHASE 8 candidate検査では実画像と照合する。提出後の検査では画像ファイルそのものは必須にせず、保存記録を照合する。

`bind-reviews` は候補の生成記録を検証し、3つのレビューへ対象PDFと入力ダイジェストを記録するだけ。passedを設定せず、画像を見る処理もない。実際の確認後だけ使う。

## 13. 重複しない記録・生成資料

| 正本 | 生成物 |
|---|---|
| SOURCES + CLAIMS | SOURCE_AUDIT.md |
| ASSIGNMENT_REQUIREMENTS + WRITING_PLAN | workflow/WRITING_BRIEF.md |
| PROFESSOR_REVIEW | PROFESSOR_EVALUATION.md |
| PROFESSOR_REVIEW.rubric | QUALITY_REVIEW.rubric（--sync-rubric） |
| 原文/組版 + 確認メモ | PROSE_DIFF.md / PROSE_CHANGES.md |

採点同期ではmet→passed、partially_met/not_met/undetermined→failed、not_applicable→not_applicableと写し、技術チェックは残す。変更があると品質記録のPDF接続をnullに戻す。教授評価そのもの、目視、技術チェックを自動合格にしない。

生成資料にはマーカーを付け、出典表・教授評価の古い内容は検査時に拒否する。品質記録がprofessor_review由来なら採点対応も一致を要求する。旧手書き資料は自動上書きしない。--replace-legacy時はquality/view-backupsへ元バイトを保存する。同じ内容の再生成はファイルを書き換えない。

HANDOFF、RESULT_TRACEABILITY、WORKLOGの内容を丸ごと自動作成する処理はない。AIが事実に基づき記録する。

## 14. 提出版と復旧

releaseは全gateが有効であることと候補監査を確認し、一時領域へPDFと5補助文書をコピーしてバイト一致を検査する。既存deliverablesをbuild/release-backupsへ移し、新版へ置換する。固定後PHASE 8が失敗すれば直前版へ復元する。STATEの書込みは一時ファイルからos.replaceで行う。

必須成果物はreport.pdf、HANDOFF.md、PROFESSOR_EVALUATION.md、SOURCE_AUDIT.md、RESULT_TRACEABILITY.md、WORKLOG.md。RUBRIC_TRACEABILITY.mdとORAL_DEFENSE.mdは実験ルートに存在すれば追加する。提出コードのファイル一覧は学習範囲管理・変更検知に使うが、releaseがコードを自動梱包する実装はない。授業でコード提出が必要なら別途対象を確認して渡す。

build/main.pdf、draft.pdf、final-candidate.pdfは提出確定版ではない。提出先へアップロードする処理はなく、本人が提出する。バックアップはGit管理外であり別端末への同期を保証しない。

## 15. 全コマンドと内部モジュール

以下の `<実験>` は実験ディレクトリ。基本的にCodexが実行する。

| コマンド | 引数・処理 |
|---|---|
| python scripts/new_experiment.py ID --title 題目 | 小文字英数字とハイフンのID、既存先拒否、雛形コピー、表紙題目設定、STATE初期化 |
| python scripts/doctor.py [--quick] | 依存確認。quickなしは全テスト・完成例再現・承認・最終検査も実施 |
| python scripts/workflow.py init <実験> [--example] | STATEを新規作成。既存STATE拒否 |
| workflow.py status <実験> | 承認有効性、学習範囲未設定、未提出/確認/意味変更待ち、次の作業 |
| workflow.py prepare-review <実験> --gate G1/G2/G3 | 前段・累積検査、確認票、待機状態 |
| workflow.py approve <実験> --gate G1/G2/G3 --decision 回答 | 対象一致と回答形式を確認し承認記録 |
| workflow.py verify <実験> | approved状態のgateだけ検証。全gate承認済みを要求するコマンドではない |
| workflow.py refresh-context <実験> | 索引ファイルの現在ハッシュを更新。読了はしない |
| workflow.py seal-data <実験> | 生データの現在ハッシュ・サイズを記録 |
| workflow.py bind-reviews <実験> | 確認記録を候補版へ接続 |
| workflow.py release <実験> | 検査済み提出一式を固定 |
| python scripts/validate_experiment.py <実験> --phase 0..8 [--candidate] [--skeleton] [--draft] | 累積検査。draftはphase 6限定 |
| python scripts/reproduce.py seal/verify <実験> | 期待出力の封印/一時コピーでの再生成一致 |
| python scripts/receive_prose.py <実験> バッチ.yaml | 原文の一括受領・差し替え |
| python scripts/review_prose.py <実験> [--slot P-001 --note 理由] [--decision 回答] | 差分表示または対象版のレビュー記録 |
| python scripts/report_views.py <実験> writing/sources/evaluation [--replace-legacy] [--sync-rubric] | 保存済み判断から表示資料を生成。syncはevaluation限定 |
| python scripts/build_report.py <実験> --mode skeleton/draft/candidate | ローカルTeX生成 |
| python scripts/render_pdf.py PDF 出力先 [--dpi 150] [--manifest 記録.yaml] | 全ページ画像と版記録 |

内部専用はworkflow_core（承認/ハッシュ）、artifact_checks（生成入力/PDF）、tex_sources（literal input/include展開）、layout_tuning（限定体裁設定）、task_scope（課題範囲の形式検査）。単体CLIは持たない。

--migration-exampleは例外的な架空例の承認記録用。example_onlyだけでなくexamples配下であることも承認照合時に確認する。実レポートの本人承認を自動代替する機能ではない。

## 16. 制限・未実装を含む正確な保証範囲

- 先取り、コメントの適切さ、本人の理解、出典本文との一致、誤字、論理、考察はAI・本人が判断する。passedやverifiedの真偽を機械が独立証明するものではない。
- AI利用statusのunknownは拒否するが、prohibited/restrictedの自然言語条件を解析して全コマンドを停止する実装ではない。実際の禁止事項は運用で守る。
- TeXはliteralなinput/includeと既定の文章枠を中心に検査し、動的入力を拒否する。一般のTeXインタプリタではない。検出可能な図表・リストの表記に限界がある。
- 空欄検出はTODO、指定待ち、未確認、未実施、二重波括弧等の文字列規則。正当な本文に同じ語がある場合にも反応し得る。
- 実験コマンドの自動生成・装置制御・全授業への対応はない。raw、processed、analysisと再現出力を要求するため、純粋な作文課題にそのまま適合するとは限らない。
- SHA-256は記録した版との一致を示す。署名、作者証明、改竄不能性、全環境での完全同一PDFを保証しない。依存パッケージは範囲指定で、完全固定ロックファイルではない。
- 通常の読み書きと一部の復元処理であり、全操作にプロセス間ロックや停電耐性があるわけではない。
- 書式を自由に変える汎用組版エンジンではない。教員指定との不一致は個別に判断する必要がある。
- トークン数の計測・予算制御は実装していない。部分参照と資料生成による省力化であり、削減率は未計測。
- GitHub Actionsはworkflow_dispatchの手動実行のみ。Python 3.12、依存導入、構文・テスト・例の再現/承認/最終検査を行う。TeXを導入する工程はなく、TeX依存の通し試験は実行環境にlatexmkがなければスキップされる。普段のローカル作業には不要。

## 17. 参照元

機械動作: [scripts](../scripts/) の全Pythonモジュール。様式: [labreport.cls](../tex/labreport.cls)、[style-contract](../config/style-contract.yaml)。入力契約: [schemas](../schemas/) と [templates](../templates/experiment/)。試験: [tests](../tests/)。人が守る運用: [AGENTS](../AGENTS.md)、[rules](../rules/)。実装と運用を同じ「自動保証」として説明しない。
