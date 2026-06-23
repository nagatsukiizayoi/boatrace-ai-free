# 履歴特徴量 core shadow connection preview 記録

## 概要

このドキュメントは、履歴特徴量の core shadow connection preview の完了内容を記録するものです。

対象ステップは以下です。

- STEP146-A: core shadow connection preview exporter 作成
- STEP146-B: core shadow connection preview checker 作成
- STEP146-C: readiness 統合

本ステップ群では、prediction core への直接接続は行っていません。

現在の接続方式は shadow-only です。

## 安全状態

現在の安全状態は以下です。

- data/history_feature_config.json は enabled:false
- connection_mode は shadow-only
- core_connection_enabled:false
- affects_prediction_output:false
- history_features_enabled:false
- docs/prediction.json は未変更
- prediction core は未接続
- 予測スコアは未変更
- 予測順位は未変更
- 推奨買い目は未変更
- 期待値は未変更

この preview は prediction output に影響しない isolated shadow path です。

## 作成・更新ファイル

STEP146-A で作成したファイル:

- scripts/export_history_feature_core_shadow_connection_preview.py
- docs/prediction_history_feature_core_shadow_connection_preview.json

STEP146-B で作成したファイル:

- scripts/check_history_feature_core_shadow_connection_preview.py

STEP146-C で更新したファイル:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

## STEP146-A exporter

STEP146-A では、prediction core に直接接続せず、shadow-only の preview JSON を生成しました。

出力ファイル:

- docs/prediction_history_feature_core_shadow_connection_preview.json

重要項目:

- step: STEP146-A
- connection_mode: shadow-only
- core_connection_enabled:false
- affects_prediction_output:false
- history_features_enabled:false
- candidate_count
- matched_candidate_count
- missing_candidate_count

期待出力:

- History feature core shadow connection preview export: OK
- STEP 146-A CHECK: OK

## STEP146-B checker

STEP146-B では、core shadow connection preview を検証する checker を作成しました。

対象ファイル:

- scripts/check_history_feature_core_shadow_connection_preview.py

この checker は以下を確認します。

- exporter が存在すること
- preview JSON が存在すること
- JSON 構文が正しいこと
- step が STEP146-A であること
- connection_mode が shadow-only であること
- core_connection_enabled:false
- affects_prediction_output:false
- history_features_enabled:false
- data/history_feature_config.json が enabled:false であること
- docs/prediction.json に差分がないこと

期待出力:

- History feature core shadow connection preview validation: OK
- STEP 146-B CHECK: OK

## STEP146-C readiness 統合

STEP146-C では、checker と preview JSON を readiness に統合しました。

対象ファイル:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

追加対象:

- scripts/check_history_feature_core_shadow_connection_preview.py
- docs/prediction_history_feature_core_shadow_connection_preview.json

history database readiness の期待出力:

- Running: python scripts/check_history_feature_core_shadow_connection_preview.py
- History feature core shadow connection preview validation: OK
- STEP 146-B CHECK: OK
- History database readiness validation: OK
- STEP 112 CHECK: OK

dashboard readiness の期待出力:

- Running: python scripts/check_history_feature_core_shadow_connection_preview.py
- Dashboard readiness outputs validation: OK

## candidate count

現時点では candidate count を診断として記録しています。

例:

- candidate_count=11
- matched_candidate_count=0
- missing_candidate_count=11

matched_candidate_count=0 は現時点では失敗ではありません。

理由:

- まだ本接続ではない
- shadow-only の preview である
- prediction output に影響しない
- candidate matching の診断段階である

## docs/prediction.json の扱い

docs/prediction.json は変更しません。

確認コマンド:

- git --no-pager diff -- docs/prediction.json

期待:

- 何も表示されない

差分が出た場合はコミット禁止です。

復元コマンド:

- git restore docs/prediction.json

## data/history_feature_config.json の扱い

data/history_feature_config.json は enabled:false を維持します。

確認コマンド:

- python scripts/check_history_feature_config.py

期待出力:

- STEP 122 CHECK: OK

## prediction core との関係

本ステップでは prediction core への直接接続はしていません。

禁止事項:

- enabled:true への変更
- prediction core への直接接続
- docs/prediction.json の変更
- 予測スコアの変更
- 予測順位の変更
- 推奨買い目の変更
- 期待値の変更
- preview JSON を prediction output に反映すること

## readiness 確認

history database readiness 確認コマンド:

- python scripts/check_history_database_readiness.py > /tmp/history_ready_146d.log
- grep -E "STEP 146-B CHECK: OK|STEP 112 CHECK: OK|History database readiness validation: OK" /tmp/history_ready_146d.log

期待:

- STEP 146-B CHECK: OK
- History database readiness validation: OK
- STEP 112 CHECK: OK

dashboard readiness 確認コマンド:

- python scripts/check_dashboard_readiness_outputs_ready.py > /tmp/dashboard_ready_146d.log
- grep -E "check_history_feature_core_shadow_connection_preview.py|Dashboard readiness outputs validation: OK" /tmp/dashboard_ready_146d.log

期待:

- Running: python scripts/check_history_feature_core_shadow_connection_preview.py
- Dashboard readiness outputs validation: OK

## rollback 方針

問題が発生した場合は、該当 step の変更を戻します。

STEP146-C を戻す場合:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

STEP146-B を戻す場合:

- scripts/check_history_feature_core_shadow_connection_preview.py

STEP146-A を戻す場合:

- scripts/export_history_feature_core_shadow_connection_preview.py
- docs/prediction_history_feature_core_shadow_connection_preview.json

ただし、docs/prediction.json と data/history_feature_config.json は変更対象ではありません。

万一変更された場合:

- git restore docs/prediction.json
- git restore data/history_feature_config.json

## 完了条件

STEP146-A から STEP146-C の完了条件は以下です。

- exporter 作成済み
- preview JSON 作成済み
- checker 作成済み
- readiness 統合済み
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- dashboard readiness OK
- history database readiness OK
- docs/prediction.json 差分なし
- data/history_feature_config.json は enabled:false
- prediction core 未接続
- 予測スコア・順位・推奨買い目・期待値未変更
- GitHub Actions 赤エラーなし
- 最終 git status clean

## 結論

STEP146-A から STEP146-C により、履歴特徴量の core shadow connection preview が作成され、checker と readiness 統合まで完了しました。

現在の状態は shadow-only です。

prediction core には接続していません。

docs/prediction.json は未変更です。

data/history_feature_config.json は enabled:false のままです。

この状態は、次段階の安全確認に進むための isolated shadow connection preview として有効です。
