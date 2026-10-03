# 日常の進め方と省力化

三つの本人承認、本人による本文執筆、根拠・原文・提出版の保全を維持する。通常、以下の操作はCodexが実行する。ユーザーがPythonや内部YAMLを操作する必要はない。

## 再開

`python scripts/workflow.py status experiments/<id>` は未提出枠、組版・確認待ち、意味変更の判断待ち、次に読む場所を短く示す。再開用の別の管理文書は作らない。状態表示は全品質検査の代わりではない。

## 骨格と執筆案内

`ASSIGNMENT_REQUIREMENTS.yaml.task_scopes` に課題ごとの実習書範囲、既習事項、後続内容の除外、指定条件、提出コード・補助コード、コメント方針を記す。G1でまとめて確認し、各文章枠の `task_ids` へ対応付ける。実習書全体の規則を読むことと、解答に先の内容を使うことは別である。

骨格時は `WRITING_PLAN.yaml.task_scope_reviews`、完成時は `PROFESSOR_REVIEW.yaml.task_scope_reviews` に、対象箇所と範囲内と判断した根拠を記す。新しい承認は増やさない。許可済みの既習知識は実習書外でも使えるが、不明な事項だけ最初に相談する。

G2準備時に `workflow/WRITING_BRIEF.md` を生成する。各枠には説明する対象、使える証拠、本人が考える点を示す。必要な枠だけ `WRITING_PLAN.yaml` の `student_judgment` に問いを書く。結論や回答例は代筆しない。結果の値は `RESULT_TRACEABILITY.md`、出典箇所は `SOURCE_AUDIT.md` を確認する。

## 本文をまとめて受領・差し替え

ユーザーは「文章1: …」「文章3を次に差し替えて: …」と送る。Codexは本人の送信内容を変えずに、次の入力を一時ファイル（例 `build/receipt.yaml`）へ保存する。末尾改行も原文どおりに保つ。YAMLの `|-` は末尾改行なし、`|` は末尾改行ありを表す。

```yaml
receipt: "2026-10-03 本人の文章1・文章3差し替えメッセージ"
paragraphs:
  - slot_id: P-001
    text: |-
      本人から届いた原文をそのまま保存する。
  - slot_id: P-003
    text: |-
      本人から届いたもう一つの原文。
```

```powershell
python scripts/receive_prose.py experiments/<id> experiments/<id>/build/receipt.yaml
```

この説明内の文章をレポートへ転用しない。受領処理はG1・G2承認を確認し、全入力を検査してから書き込む。旧原文・旧組版・旧対応表・受領元は `prose/history/` に残る。旧組版を退避するため、新原文が下書きへ無断で混入しない。書き込み例外時は原文・組版・対応表を復元する。OS停止中の完全なトランザクション保証ではない。保存中断時は履歴を確認してから再開する。

続けてCodexが原文を校正・組版し、読み比べ後に記録する。

```powershell
python scripts/review_prose.py experiments/<id> --slot P-001 --note "『実効』を『実行』へ訂正。数値・否定・因果・結論は変更なし。"
python scripts/build_report.py experiments/<id> --mode draft
```

確認メモは実際に変更した内容を書く。本人へは日本語の変更説明 `quality/PROSE_CHANGES.md` を示し、必要時だけ詳細 `PROSE_DIFF.md` を開く。原文との意味の同一性を自動保証したとは言わない。意味・数値等の変更は、これまでどおり具体的な本人承認を記録する。

## 記録は一度、表示は自動生成

```powershell
python scripts/report_views.py experiments/<id> sources
python scripts/report_views.py experiments/<id> evaluation --sync-rubric
```

前者は検証済みの出典・主張記録から `SOURCE_AUDIT.md` を生成する。後者は実際に行った教授視点評価から `PROFESSOR_EVALUATION.md` と品質記録の採点対応を生成する。技術チェック、PDF目視、本人確認は代行しない。同期で評価内容が変わるとPDFへの確認接続を解除するため、実際に確認後、従来どおり `workflow.py bind-reviews` を行う。

既存の手書き文書は自動上書きしない。独自の注記を移した後だけ `--replace-legacy` を指定する。旧版は `quality/view-backups/` に保存される。既存の完成例や承認を新機能導入だけのために変更する必要はない。

## 軽微な体裁調整

骨格の図幅を `width=\ReportFigureWidth` としておけば、G2後の最終配置を任意の `spec/LAYOUT_TUNING.yaml` で調整できる。

```yaml
figure_width: 0.85
textfloatsep_pt: 14
floatsep_pt: 12
```

図幅は行幅の0.6〜1.0倍、間隔は順に10〜20pt、8〜18ptに限定する。指定したファイルがある場合に調整間隔を適用し、ない場合は従来の共通クラスの伸縮間隔を使う。指定のない図は影響を受けない。骨格は既定設定で保存し、候補だけを再生成・確認する。G2は維持、旧候補・G3は失効する。軸、目盛、結果、図表内容、見出しを変える抜け道ではない。授業の指定に反する調整は禁止する。

## 確認と終了

本人には実施事実、原文の意図、重要な選択、完成PDFを頼む。依頼は対象・見る点・必要な判断を示し、変更のない回答は再質問しない。Codexは数値・単位・出典・参照・技術面を確認する。

初回全読、出典本文の確認、最終PDF全ページ確認は維持する。途中の再確認は変更の影響範囲に限定し、最終候補の確認記録をその版に接続する。必須違反・根拠不足・誤りは修正する。任意の改善案は上位3件まで示して本人が選び、好みの差だけなら完成を止めない。

通常のレポート制作ではフレームワーク全テストを繰り返さない。自動検査のコストとAIのトークン消費を混同せず、重複する全文再読・作文・質問を減らす。
