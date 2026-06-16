# 履歴特徴量 prediction core 接続ポイント最終監査 記録

## 概要

本ドキュメントは、履歴特徴量を prediction core に接続する前に実施した、接続ポイント最終監査の記録です。

この監査では、prediction writer 候補、prediction core 参照箇所、history feature adapter / shadow preview の使用箇所、config guard の参照箇所を確認しました。

重要な点として、この段階では prediction core への接続は行っていません。

enabled:true への変更も行っていません。

docs/prediction.json、予測スコア、順位、推奨買い目、期待値も変更していません。

## 対象ステップ

- STEP143-A: prediction core 接続ポイント最終監査
- STEP143-B: 接続ポイント最終監査結果ドキュメント化

## 監査ログ

監査ログは以下に保存しました。

/tmp/history_feature_143a/

主なログ:

- prediction_core_refs.txt
- prediction_writer_candidates.txt
- history_feature_usage_refs.txt
- config_guard_refs.txt
- prediction_json_sha256_before.txt
- prediction_json_sha256_after.txt
- config_enabled_check.txt
- pre_connection_checks.txt
- history_readiness.log
- history_readiness_summary.txt
- dashboard_readiness.log
- dashboard_readiness_summary.txt
- git_status_final.txt
- prediction_core_connection_point_audit_summary.txt

## prediction core references

以下の観点で参照検索を行いました。

- prediction.json
- recommendations
- expected_value
- expectedValue
- score
- rank
- prediction_final

結果は以下に保存しました。

/tmp/history_feature_143a/prediction_core_refs.txt

## prediction writer candidates

docs/prediction.json や prediction_final.json を生成または補正する可能性がある候補を検索しました。

結果は以下に保存しました。

/tmp/history_feature_143a/prediction_writer_candidates.txt

接続ポイント候補として、実際の prediction writer を引き続き確認対象にします。

## history feature usage refs

history_feature、shadow_preview、adapter_preview の使用箇所を検索しました。

結果は以下に保存しました。

/tmp/history_feature_143a/history_feature_usage_refs.txt

主な確認対象:

- scripts/export_history_feature_shadow_preview.py
- scripts/check_history_feature_shadow_preview.py
- scripts/check_dashboard_history_feature_shadow_preview.py
- docs/index.html
- readiness scripts

## config guard refs

history_feature_config.json、enabled、history_features_enabled、affects_prediction_output などの参照箇所を検索しました。

結果は以下に保存しました。

/tmp/history_feature_143a/config_guard_refs.txt

注意点として、docs 内の enabled:true という文字列は説明用であれば即 NG ではありません。

実際の data/history_feature_config.json が enabled:false であることが重要です。

## config 状態

data/history_feature_config.json は enabled:false を維持しています。

確認結果:

CONFIG_ENABLED_FALSE_OK

## docs/prediction.json の確認

docs/prediction.json について、監査前後の SHA256 を保存しました。

- prediction_json_sha256_before.txt
- prediction_json_sha256_after.txt

before / after の hash が一致していることを確認しました。

一部 readiness 実行時に既存 dashboard compatibility 処理が docs/prediction.json を一時的に補正する場合がありますが、その場合は git restore docs/prediction.json により戻しています。

最終状態では docs/prediction.json は未変更です。

## 実行した主要チェック

以下を実行しました。

- python scripts/check_history_feature_config.py
- python scripts/check_history_feature_shadow_preview.py
- python scripts/check_dashboard_history_feature_shadow_preview.py
- python scripts/check_history_feature_adapter_preview.py
- python scripts/check_dashboard_history_feature_adapter_preview.py

確認された OK 行:

- STEP 122 CHECK: OK
- STEP 141-B CHECK: OK
- STEP 141-E CHECK: OK
- STEP 137-G CHECK: OK
- STEP 138-A CHECK: OK

## readiness checks

history database readiness を実行しました。

確認された OK 行:

- STEP 141-B CHECK: OK
- STEP 141-E CHECK: OK
- History database readiness validation: OK
- STEP 112 CHECK: OK

dashboard readiness を実行しました。

確認された OK 行:

- Running: python scripts/check_history_feature_shadow_preview.py
- Running: python scripts/check_dashboard_history_feature_shadow_preview.py
- Dashboard readiness outputs validation: OK

## 接続ポイント候補

今後、prediction core へ最小安全接続する場合の確認候補は以下です。

- scripts/ensure_prediction_json_dashboard_compat.py
- scripts/history_feature_prediction_adapter.py
- scripts/export_history_feature_shadow_preview.py
- prediction_writer_candidates.txt に記録された実際の prediction writer 候補

ただし、scripts/ensure_prediction_json_dashboard_compat.py は dashboard compatibility 補正用であり、履歴特徴量接続ポイントとして直接使うかは慎重に判断します。

## 変更していないもの

以下は変更していません。

- data/history_feature_config.json
- docs/prediction.json
- docs/prediction_history_feature_shadow_preview.json
- docs/prediction_history_feature_adapter_preview.json
- docs/index.html
- scripts/*.py
- prediction core
- 予測スコア
- 予測順位
- 推奨買い目
- 期待値

## 安全方針

今回の監査時点では以下を維持しています。

- enabled:false
- prediction core 未接続
- docs/prediction.json 未変更
- prediction output unchanged
- shadow preview only
- score / rank / recommendation / expected value unchanged

## 次の段階に進む前の注意

prediction core へ接続する前に、以下を再確認します。

- 実際の prediction writer がどのファイルか
- 接続は enabled:false guard の内側で行うこと
- shadow preview と同じデータ構造を使うこと
- prediction output に影響しない dry-run / shadow path を先に維持すること
- docs/prediction.json の差分がないこと
- rollback 可能な stable tag が存在すること

## 結論

STEP143-A の監査により、履歴特徴量を prediction core に接続する前の参照箇所と候補ファイルを確認しました。

現時点ではまだ接続は行っていません。

現在の状態は以下です。

shadow preview only
enabled:false
prediction output unchanged
prediction core unmodified

以上により、prediction core 接続ポイント最終監査は完了です。
