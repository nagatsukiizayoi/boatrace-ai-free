# 履歴特徴量連携メモ

## 目的

このドキュメントは、Google Sheets 由来の過去レースデータから履歴データベースを構築し、選手別履歴特徴量を作成して、将来の予測精度向上に利用するための設計と運用手順をまとめるものです。

現時点では、履歴特徴量は予測処理に直接反映していません。  
`data/history_feature_config.json` の `enabled` は `false` です。

---

## 現在の状態

履歴特徴量は、以下の段階まで準備済みです。

1. Google Sheets から過去データを取得
2. 年別 results CSV に正規化
3. SQLite DB を構築
4. DB 内容を検証
5. 選手別履歴特徴量 CSV を作成
6. 選手別履歴特徴量サマリー JSON を出力
7. 予測接続用設定ファイルを作成
8. 統合チェックと GitHub Actions に組み込み

---

## 主なファイル

### 入力・設定

| ファイル | 用途 |
|---|---|
| `data/history_sources.json` | Google Sheets と公式データ候補の定義 |
| `data/google_sheets_column_mapping.json` | Google Sheets 列名から標準列名への対応 |
| `data/history_feature_config.json` | 予測処理で履歴特徴量を使うための設定 |

### 年別CSV

| ファイル | 用途 |
|---|---|
| `data/import/history/results/results_2023.csv` | 2023年の正規化済みレース結果 |
| `data/import/history/results/results_2024.csv` | 2024年の正規化済みレース結果 |
| `data/import/history/results/results_2025.csv` | 2025年の正規化済みレース結果 |
| `data/import/history/results/results_2026.csv` | 2026年の正規化済みレース結果 |

### SQLite DB

| ファイル | 用途 |
|---|---|
| `db/boatrace.sqlite3` | ローカル生成される履歴DB。通常は Git 管理外 |
| `data/import/history/history_database_summary.json` | DB構築結果のサマリー |
| `docs/history_database_summary.json` | ダッシュボード用履歴DBサマリー |

### 選手履歴特徴量

| ファイル | 用途 |
|---|---|
| `data/import/history/racer_history_features.csv` | 選手別履歴特徴量 |
| `docs/racer_history_features_summary.json` | ダッシュボード用選手特徴量サマリー |

---

## 選手履歴特徴量の列

`data/import/history/racer_history_features.csv` には以下の列があります。

| 列 | 意味 |
|---|---|
| `racer_id` | 選手ID |
| `racer_name` | 選手名 |
| `race_count` | 集計対象の出走数 |
| `win_count` | 1着回数 |
| `top2_count` | 2連対回数 |
| `top3_count` | 3連対回数 |
| `win_rate` | 勝率 |
| `top2_rate` | 2連対率 |
| `top3_rate` | 3連対率 |
| `avg_start_timing` | 平均スタートタイミング |
| `last_race_date` | 最終出走日 |

---

## `history_feature_config.json` の意味

`data/history_feature_config.json` は、予測処理が履歴特徴量を使う際の設定ファイルです。

現時点では以下のようになっています。

```json
"enabled": false
