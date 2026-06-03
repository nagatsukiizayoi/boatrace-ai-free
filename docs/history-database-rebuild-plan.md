# 履歴データベース再構築計画

この文書は、ボートレース過去データを年別CSVとして整理し、現在の予測プログラムに最適化したSQLiteデータベースへ再構築するための計画をまとめるものです。

## 基本方針

データ収集、データ整形、履歴DB構築は、予測本体とは分離して管理します。

現段階では完全な別リポジトリにはせず、同じリポジトリ内の別スクリプトとして管理します。

## 採用方針

- 同じリポジトリ内で管理する
- ただし予測本体とは別スクリプトにする
- CSVは年ごとに分ける
- rawデータとimportデータを分ける
- DBはCSVから再構築可能にする

## 理由

- 予測本体を重くしない
- データ収集失敗と予測失敗を切り分けやすい
- 年別CSVと相性が良い
- GitHub Actionsを分けやすい
- DB schemaと連携しやすい
- 将来、必要になればデータ収集部分だけ別リポジトリ化できる

## データの種類

履歴データは以下に分けます。

| 種別 | 内容 |
|---|---|
| races | レース単位の情報 |
| race_entries | 出走表、選手、モーター、ボート情報 |
| odds | オッズ情報 |
| results | レース結果、着順、払戻金 |
| predictions | 過去の予測結果 |
| bet_results | 購入結果、的中、不的中、収支 |
| racer_term_stats | レーサー期別成績 |

## CSV分割方針

大量データを扱うため、CSVは年ごとに分けます。

例:

```text
data/import/history/races/races_2026.csv
data/import/history/race_entries/race_entries_2026.csv
data/import/history/odds/odds_2026.csv
data/import/history/results/results_2026.csv
data/import/history/predictions/predictions_2026.csv
data/import/history/bet_results/bet_results_2026.csv

