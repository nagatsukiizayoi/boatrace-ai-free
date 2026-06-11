# 履歴特徴量 adapter preview ダッシュボード統合 完了記録

## 概要

このドキュメントは、STEP138-A および STEP138-B で実施した、履歴特徴量 adapter preview のダッシュボード表示および readiness 統合の完了内容を記録する。

adapter preview は、STEP137-D から STEP137-H で整備した履歴特徴量 adapter dry-run と adapter preview JSON を、ダッシュボード上で確認できるようにするための安全な表示機能である。

現時点では、履歴特徴量は予測ロジック本体には接続していない。

## 対象ステップ

- STEP137-D: 履歴特徴量 prediction adapter dry-run 実装
- STEP137-E: adapter dry-run check を統合 readiness に追加
- STEP137-F: adapter preview JSON 出力
- STEP137-G: adapter preview JSON 検証スクリプト追加
- STEP137-H: adapter preview check を統合 readiness に追加
- STEP138-A: adapter preview を dashboard に表示
- STEP138-B: adapter preview dashboard check を readiness に統合

## 作成・更新ファイル

STEP138-A / STEP138-B で主に以下を更新した。

- docs/index.html
- scripts/check_dashboard_history_feature_adapter_preview.py
- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

既存の adapter preview 関連ファイルは以下である。

- scripts/history_feature_prediction_adapter.py
- scripts/check_history_feature_prediction_adapter.py
- scripts/export_history_feature_adapter_preview.py
- scripts/check_history_feature_adapter_preview.py
- docs/prediction_history_feature_adapter_preview.json

## 現在の安全状態

現在も履歴特徴量は disabled のままである。

JSON 表記:

    {
      "enabled": false
    }

この状態により、以下は変更されていない。

- docs/prediction.json
- 予測スコア
- 予測順位
- 推奨買い目
- 期待値
- 既存の prediction 出力構造
- 本番予測ロジック

## adapter preview の安全フラグ

adapter preview JSON では、予測本体に影響しないことを示す安全フラグを保持する。

主な確認項目は以下である。

- history_features_enabled: false
- affects_prediction_output: false
- prediction_output_modified: false
- prediction_json_modified: false
- source_prediction: docs/prediction.json
- source_adapter: scripts/history_feature_prediction_adapter.py

## dashboard 表示

STEP138-A により、docs/index.html に adapter preview 表示セクションを追加した。

この表示は診断・確認用であり、予測結果そのものを変更しない。

表示対象は以下である。

- docs/prediction_history_feature_adapter_preview.json
- candidate_count
- matched_candidate_count
- missing_candidate_count
- loaded_feature_racer_count
- history_features_enabled
- affects_prediction_output
- prediction_output_modified
- prediction_json_modified

## dashboard check

STEP138-A で以下の検証スクリプトを追加した。

- scripts/check_dashboard_history_feature_adapter_preview.py

このチェックでは以下を確認する。

- docs/index.html に adapter preview セクションがあること
- docs/prediction_history_feature_adapter_preview.json を参照していること
- 安全フラグを表示または参照していること
- dashboard 表示が prediction 出力を変更しないこと

期待される出力は以下である。

    Dashboard history feature adapter preview validation: OK
    STEP 138-A CHECK: OK

## readiness 統合

STEP138-B により、以下の readiness に adapter preview dashboard check を統合した。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

これにより、統合 readiness の中で以下が確認できる。

    STEP 138-A CHECK: OK
    STEP 112 CHECK: OK

## 実行確認済みチェック

以下の確認を実施済みである。

    python scripts/check_dashboard_history_feature_adapter_preview.py
    python scripts/check_dashboard_readiness_outputs_ready.py
    python scripts/check_history_database_readiness.py

期待される主な出力は以下である。

    Dashboard history feature adapter preview validation: OK
    STEP 138-A CHECK: OK
    History database readiness validation: OK
    STEP 112 CHECK: OK

## GitHub Actions

push 後、以下の GitHub Actions を確認対象とする。

- Check Dashboard Final Readiness
- Check History Database Readiness
- pages-build-deployment

赤エラーがないことを確認する。

## 変更しないファイル

STEP138-A / STEP138-B では以下を変更しない。

- data/history_feature_config.json
- docs/prediction.json
- docs/prediction_history_feature_preview.json
- docs/prediction_history_feature_ab_preview.json
- docs/prediction_history_feature_adapter_preview.json

## enabled:true に進む前の注意

履歴特徴量を予測ロジック本体に接続する前に、以下を確認する必要がある。

- adapter preview と A/B preview の差分確認
- default values の影響確認
- racer_id 正規化の妥当性確認
- missing_candidate_count の扱い確認
- dashboard 表示の安定性確認
- readiness と GitHub Actions の継続成功確認
- rollback 可能な stable tag の存在確認

## rollback 方針

問題が発生した場合は、以下の stable tag へ戻す。

- history-feature-adapter-dry-run-stable
- history-feature-pre-enable-audit-stable
- history-feature-ab-preview-stable

## 結論

STEP138-A / STEP138-B により、履歴特徴量 adapter preview のダッシュボード表示と readiness 統合が完了した。

現時点では、履歴特徴量は preview / diagnostics / readiness 用であり、予測ロジック本体には未接続である。

次のステップでは、adapter preview dashboard 統合後の安定状態をタグ付けし、以後の final diff audit または prediction core 接続前検証に進む。
