# 履歴特徴量準備版 完了記録

このドキュメントは、Boatrace AI Free における履歴データベースおよび履歴特徴量準備版の構築完了状態を記録するものです。

## 完了状態

履歴データの取得、整形、SQLite データベース構築、選手別履歴特徴量の生成、ダッシュボード向け JSON 出力、統合チェック、GitHub Actions による自動確認まで完了しています。

現時点では、履歴特徴量は **予測ロジックへ直接反映されていません**。

`data/history_feature_config.json` の設定は以下の状態です。

```json
"enabled": false

## ダッシュボード表示追加

履歴DBおよび選手別履歴特徴量のサマリーは、ダッシュボード上でも確認できるようになっています。

追加された表示内容は以下です。

- 履歴DBの利用可能状態
- 総行数
- 総レース数
- データ期間
- 会場数
- 選手数
- 選手履歴特徴量の選手数
- 総出走数
- 平均勝率
- 平均3連対率
- 出走数上位選手
- 勝率上位選手
- 3連対率上位選手

対象ファイルは以下です。

- docs/index.html
- docs/history_database_summary.json
- docs/racer_history_features_summary.json

表示確認用チェックは以下です。

- python scripts/check_dashboard_history_feature_summary.py

期待出力は以下です。

- Dashboard history feature summary validation: OK
- STEP 129-A CHECK: OK

このチェックは、統合 readiness チェックにも追加されています。

- python scripts/check_history_database_readiness.py

そのため、GitHub Actions の Check History Database Readiness でも、ダッシュボード上の履歴特徴量サマリー表示が自動確認されます。

## 追加完了 STEP

履歴特徴量準備版の完了後、以下の追加 STEP も完了しています。

- STEP129-A: 履歴DB・履歴特徴量サマリーをダッシュボードに表示
- STEP130: ダッシュボード履歴特徴量表示チェックを統合 readiness チェックに追加

## 予測結果への影響

このダッシュボード表示追加は、既存の予測ロジックには影響しません。

data/history_feature_config.json は引き続き以下の状態です。

- enabled: false

そのため、履歴特徴量は画面上で確認できるようになりましたが、予測結果にはまだ反映されていません。

安全状態は維持されています。
