# 履歴特徴量 shadow preview ダッシュボード統合 完了記録

## 概要

本ドキュメントは、履歴特徴量 shadow preview の生成、検証、readiness 統合、dashboard 表示統合が完了したことを記録するものです。

shadow preview は prediction core へ履歴特徴量を接続する前に、安全に候補データ、欠損状況、安全フラグを確認するための preview です。

重要な点として、shadow preview は docs/prediction.json を変更せず、予測スコア、順位、推奨買い目、期待値には影響しません。

## 対象ステップ

- STEP141-A: 履歴特徴量 shadow preview exporter 作成
- STEP141-B: shadow preview 検証スクリプト作成
- STEP141-C: history database readiness への shadow preview check 統合
- STEP141-D: dashboard readiness への shadow preview check 統合
- STEP141-E: dashboard への shadow preview 表示追加
- STEP141-F: dashboard shadow preview 表示検証を readiness checks に統合

## 作成・更新された主なファイル

- scripts/export_history_feature_shadow_preview.py
- docs/prediction_history_feature_shadow_preview.json
- scripts/check_history_feature_shadow_preview.py
- scripts/check_dashboard_history_feature_shadow_preview.py
- docs/index.html
- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

## 現在の安全状態

data/history_feature_config.json は enabled:false を維持しています。

現在の状態:

{ "enabled": false }

履歴特徴量はまだ prediction core には接続されていません。

## 変更していないもの

以下は変更していません。

- docs/prediction.json
- docs/prediction_history_feature_preview.json
- docs/prediction_history_feature_ab_preview.json
- docs/prediction_history_feature_adapter_preview.json
- prediction core 実装
- 予測スコア
- 予測順位
- 推奨買い目
- 期待値
- 購入金額
- 本番出力ロジック

## shadow preview の目的

shadow preview の目的は以下です。

- 履歴特徴量候補が生成できることを確認する
- racer_id または選手 ID の対応を確認する
- candidate_count を確認する
- matched_candidate_count を確認する
- missing_candidate_count を確認する
- prediction output に影響しないことを確認する
- dashboard で安全に可視化できることを確認する
- readiness checks に統合しても既存チェックを壊さないことを確認する

## dashboard 表示

docs/index.html に shadow preview 表示セクションを追加しました。

参照 JSON:

docs/prediction_history_feature_shadow_preview.json

主な表示項目:

- schema_version
- step
- candidate_count
- matched_candidate_count
- missing_candidate_count
- history_features_enabled
- affects_prediction_output
- prediction_json_unchanged または同等の安全状態
- shadow_preview_only または同等の安全状態

## 検証スクリプト

shadow preview 自体の検証:

python scripts/check_history_feature_shadow_preview.py

期待出力:

History feature shadow preview validation: OK
STEP 141-B CHECK: OK

dashboard 表示の検証:

python scripts/check_dashboard_history_feature_shadow_preview.py

期待出力:

Dashboard history feature shadow preview validation: OK
STEP 141-E CHECK: OK

## readiness 統合

history database readiness には以下が統合済みです。

- scripts/check_history_feature_shadow_preview.py
- scripts/check_dashboard_history_feature_shadow_preview.py

dashboard readiness には以下が統合済みです。

- scripts/check_history_feature_shadow_preview.py
- scripts/check_dashboard_history_feature_shadow_preview.py

## readiness 期待出力

history database readiness:

python scripts/check_history_database_readiness.py

期待される主な出力:

History feature shadow preview validation: OK
STEP 141-B CHECK: OK
Dashboard history feature shadow preview validation: OK
STEP 141-E CHECK: OK
History database readiness validation: OK
STEP 112 CHECK: OK

dashboard readiness:

python scripts/check_dashboard_readiness_outputs_ready.py

期待される主な出力またはログ:

Running: python scripts/check_history_feature_shadow_preview.py
Running: python scripts/check_dashboard_history_feature_shadow_preview.py
Dashboard readiness outputs validation: OK

dashboard readiness 側では子スクリプトの標準出力が直接表示されない場合があります。その場合でも、個別チェックで STEP 141-B CHECK: OK と STEP 141-E CHECK: OK が確認できていれば問題ありません。

## GitHub Actions 確認項目

push 後に以下の GitHub Actions が赤エラーなしで完了していることを確認します。

- Check Dashboard Final Readiness
- Check History Database Readiness
- pages-build-deployment

## docs/prediction.json について

一部 readiness 実行時に、既存の dashboard compatibility スクリプトにより docs/prediction.json が一時的に補正される場合があります。

その場合は shadow preview 由来の変更ではないため、必ず以下で戻します。

git restore docs/prediction.json

STEP141-A から STEP141-F の完了状態では、docs/prediction.json はコミットされておらず、最終状態は clean です。

## 安全フラグ

現在の安全方針は以下です。

- enabled:false を維持
- shadow preview は別 JSON にのみ出力
- dashboard 表示は参照のみ
- prediction core には未接続
- prediction output には影響しない
- score / rank / recommendation / expected value は変更しない

## 完了条件

STEP141-A から STEP141-F では以下を満たしました。

- shadow preview exporter 作成
- shadow preview JSON 生成
- shadow preview validation 作成
- history database readiness 統合
- dashboard readiness 統合
- dashboard 表示追加
- dashboard 表示 validation 作成
- dashboard 表示 validation の readiness 統合
- STEP 141-B CHECK: OK
- STEP 141-E CHECK: OK
- STEP 112 CHECK: OK
- GitHub Actions 赤エラーなし
- git status clean
- data/history_feature_config.json は enabled:false
- docs/prediction.json 未変更
- prediction core 未変更

## 次の段階に進む前の注意

prediction core へ接続する前に、少なくとも以下を再確認します。

- docs/prediction.json の差分がないこと
- shadow preview の matched / missing 件数が妥当であること
- adapter preview と shadow preview の差分が説明可能であること
- racer_id / 選手 ID の対応が安定していること
- enabled:false を維持したまま readiness が成功すること
- rollback 可能な stable tag が存在すること

## 結論

STEP141-A から STEP141-F により、履歴特徴量 shadow preview は dashboard 上で安全に確認できる状態になりました。

ただし、これはまだ prediction core への接続ではありません。

現時点では以下の状態です。

shadow preview only
enabled:false
prediction output unchanged
prediction core unmodified

以上により、履歴特徴量 shadow preview dashboard 統合は完了です。
