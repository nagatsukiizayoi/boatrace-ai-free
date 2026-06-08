# 履歴特徴量 A/B 比較設計書

このドキュメントは、履歴特徴量を予測ロジックへ本格的に反映する前に、A/B 比較を行うための設計方針を記録するものです。

現時点では、履歴特徴量は dry-run まで完了していますが、予測結果にはまだ反映していません。

## 現在の安全状態

現在、data/history_feature_config.json は以下の状態です。

```json
"enabled": false

## A/B preview 実装完了記録

### 実施済みステップ

以下の A/B preview 関連ステップを完了した。

- STEP135-B: A/B preview schema 定義
- STEP135-C: A/B preview schema チェックを統合 readiness に追加
- STEP135-D: A/B preview JSON 出力
- STEP135-E: A/B preview JSON 検証スクリプト追加
- STEP135-F: A/B preview 検証を統合 readiness に追加
- STEP135-G: A/B preview をダッシュボードに表示
- STEP135-H: ダッシュボード A/B preview 表示チェックを統合 readiness に追加

### 追加・更新された主なファイル

- `docs/history-feature-ab-preview-schema.json`
- `scripts/check_history_feature_ab_preview_schema.py`
- `scripts/export_history_feature_ab_preview.py`
- `docs/prediction_history_feature_ab_preview.json`
- `scripts/check_history_feature_ab_preview.py`
- `scripts/check_dashboard_history_feature_ab_preview.py`
- `docs/index.html`
- `scripts/check_history_database_readiness.py`

### 現在の安全状態

`data/history_feature_config.json` は引き続き以下の状態である。

```json
{
  "enabled": false
}
