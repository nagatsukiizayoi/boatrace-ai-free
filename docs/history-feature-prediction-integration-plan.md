# 履歴特徴量 予測ロジック接続設計書

このドキュメントは、履歴特徴量を将来的に予測ロジックへ接続するための設計方針を記録するものです。

現時点では、履歴特徴量は準備済みですが、予測結果にはまだ反映していません。

## 現在の安全状態

履歴データベース、選手別履歴特徴量、ダッシュボード表示、統合 readiness チェック、GitHub Actions 連携は完了しています。

ただし、data/history_feature_config.json は現在 enabled:false の状態です。

そのため、履歴特徴量は予測結果には影響しません。

現在の状態は、既存予測ロジックを壊さない安全な準備状態です。

## 主な関連ファイル

設定ファイル:

- data/history_feature_config.json

履歴特徴量:

- data/import/history/racer_history_features.csv
- docs/racer_history_features_summary.json
- docs/history_database_summary.json

ダッシュボード:

- docs/index.html
- scripts/check_dashboard_history_feature_summary.py

統合チェック:

- scripts/check_history_database_readiness.py
- scripts/check_history_feature_config.py

予測関連 JSON:

- docs/prediction.json
- docs/prediction_final.json
- docs/prediction_runs.json
- docs/bet_results_summary.json

## 使用予定の特徴量

将来的に利用する候補は以下です。

- race_count
- win_count
- top2_count
- top3_count
- win_rate
- top2_rate
- top3_rate
- avg_start_timing
- last_race_date

## 結合方針

履歴特徴量は racer_id をキーとして予測対象データへ結合します。

予測対象データ側に racer_id が存在し、racer_history_features.csv 側にも同じ racer_id がある場合、その選手の履歴特徴量を使用します。

racer_id が存在しない場合、または履歴特徴量が見つからない場合は、デフォルト値を使います。

## 欠損時の方針

欠損選手には data/history_feature_config.json の default_values を使います。

想定する初期値は以下です。

- race_count: 0
- win_rate: 0.0
- top2_rate: 0.0
- top3_rate: 0.0
- avg_start_timing: null
- last_race_date: null

これにより、履歴データがない選手がいても予測処理を停止させない方針です。

## enabled フラグ

現在は enabled:false です。

enabled:false の場合:

- 履歴特徴量は準備済み
- ダッシュボードでは確認可能
- 予測結果には反映しない
- 既存予測ロジックを維持する

enabled:true にする前には、以下を確認します。

- 予測ロジックが履歴特徴量を読み込める
- racer_id による結合が成功する
- 欠損時のデフォルト値が適用される
- docs/prediction_final.json など既存 JSON の構造が壊れない
- ダッシュボードチェックが成功する
- GitHub Actions が成功する
- A/B 比較ができる

## A/B 比較方針

履歴特徴量を予測へ反映する前に、A/B 比較を行います。

比較対象は以下です。

- 履歴特徴量なしの予測
- 履歴特徴量ありの予測
- 予測順位の変化
- 推奨買い目の変化
- 期待値表示の変化
- 過度な偏りの有無

比較が完了するまでは enabled:true にしません。

## 段階的な実装予定

### STEP134-A

この設計書を作成します。

### STEP134-B

履歴特徴量を読み込む補助処理を作成します。

この段階では、まだ予測結果には反映しません。

### STEP134-C

予測対象データと履歴特徴量を racer_id で結合できるか検証します。

### STEP134-D

履歴特徴量あり・なしの A/B 比較用出力を作成します。

### STEP134-E

enabled:false のまま dry-run を行います。

### STEP134-F

小さな補正係数で試験的に予測へ反映します。

## ロールバック方針

問題が起きた場合は、まず data/history_feature_config.json を enabled:false に戻します。

必要に応じて、以下の安定タグに戻します。

- history-feature-prepared-stable
- history-feature-completion-stable
- history-feature-dashboard-stable

## 現時点の結論

履歴特徴量は予測ロジックへ接続する準備が整っています。

ただし、現在は安全性を優先し、enabled:false のまま維持します。

次の段階では、まず予測結果に影響しない形で STEP134-B の読み込み処理を作成することが推奨されます。
