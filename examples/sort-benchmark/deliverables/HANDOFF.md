# HANDOFF

## 実施内容

- 過去レポートの意匠を使わず、A4・1段組・本文10.5pt・25mm余白の新様式を作成した。
- 架空のソート計測値40件を用い、平均・標準偏差・比較比を再生成する分析処理を作成した。
- 表、対数軸の図、数式、コード、Web参考文献を含む完成例を作成した。

## 重視した点と判断根拠

- 表紙内容を実験ごとのYAMLへ分離し、本文で表紙情報を再掲しなかった。
- 図表を本文で先に参照し、`[tbp]` フロートとして配置した。
- 日本語の公式文書を優先し、該当しない計算量情報だけ英語の公的機関資料を使用した。
- 数値は架空であることを表紙、目的、表キャプション、考察、結論で明示した。

## 実験結果

- 8,000件での平均時間はバブル194.74 ms、クイック2.3718 ms、比は82.1であった。
- 入力サイズが1,000件から8,000件へ増えたときの平均時間増加率は、それぞれ約62.4倍と10.1倍であった。

## レポートへの反映

- 結果節では観測値と傾向だけを述べ、計算量との比較は考察節へ分けた。
- 架空値から計算量を証明したとは書かず、NISTの説明との整合に表現を限定した。
- 主要数値は `RESULT_TRACEABILITY.md` から生データと計算へ追跡できる。

## ユーザー確認事項・未解決事項

- 数値は表示確認専用であり、実在環境の性能評価には使用できない。
- 実際の授業では、実習書の表紙指定、章構成、提出形式が本フレームワークより優先される。

## 再生成方法

```powershell
python examples/sort-benchmark/analysis/analyze.py
python scripts/build_report.py examples/sort-benchmark
python scripts/validate_experiment.py examples/sort-benchmark --phase 8
```

## 提出ファイル

- `deliverables/report.pdf`
- `deliverables/HANDOFF.md`
- `deliverables/SOURCE_AUDIT.md`
- `deliverables/RESULT_TRACEABILITY.md`
- `deliverables/WORKLOG.md`
