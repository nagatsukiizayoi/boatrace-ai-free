# 履歴特徴量 prediction core 接続候補 調査結果

## 概要

このドキュメントは、STEP140-A で実施した prediction core 接続候補の調査結果を記録する。

目的は、履歴特徴量を将来的に prediction core へ接続する場合に、どのファイル・処理が最小変更ポイントになり得るかを把握することである。

現時点では、履歴特徴量は prediction core に接続していない。

## 現在の安全状態

data/history_feature_config.json は現在も disabled のままである。

    {
      "enabled": false
    }

以下は実施していない。

- enabled:true への変更
- docs/prediction.json の変更
- 予測スコア計算への履歴特徴量反映
- 予測順位への履歴特徴量反映
- 推奨買い目への履歴特徴量反映
- 期待値計算への履歴特徴量反映
- prediction core の変更

## STEP140-A で実施した調査

STEP140-A では、以下の観点で調査した。

- prediction writer / generator の再確認
- prediction core 候補ファイル一覧の作成
- 履歴特徴量 adapter 使用箇所の確認
- racer_id / 選手 ID 使用箇所の確認
- config guard 使用箇所の確認
- 重要ファイルの先頭確認
- docs/prediction.json の sha256 保存
- git diff / git status が clean であることの確認

調査ログは以下に保存した。

- /tmp/history_feature_140a/prediction_writer_generator_refs.txt
- /tmp/history_feature_140a/prediction_core_candidate_files.txt
- /tmp/history_feature_140a/history_adapter_usage_refs.txt
- /tmp/history_feature_140a/racer_id_refs.txt
- /tmp/history_feature_140a/config_guard_refs.txt
- /tmp/history_feature_140a/ensure_prediction_json_dashboard_compat_head.txt
- /tmp/history_feature_140a/history_feature_prediction_adapter_head.txt
- /tmp/history_feature_140a/export_history_feature_adapter_preview_head.txt
- /tmp/history_feature_140a/prediction_json_sha256.txt
- /tmp/history_feature_140a/git_diff_stat.txt
- /tmp/history_feature_140a/git_status.txt

## prediction writer / generator 候補

STEP140-A では、docs/prediction.json や prediction.json、recommendations、expected_value、score、rank などをキーワードに検索した。

重要な候補は以下である。

- scripts/ensure_prediction_json_dashboard_compat.py
- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py
- docs/index.html
- GitHub Actions workflows

特に scripts/ensure_prediction_json_dashboard_compat.py は、dashboard compatibility のために docs/prediction.json を補正する既存処理である。

STEP139-A/B で確認した通り、この補正処理は no-change audit 時には注意が必要である。

## prediction core 候補ファイル

STEP140-A の候補検索では、expected_value、score、recommendation、recommendations、odds、rank、prediction_final などを含むファイルを抽出した。

候補ファイルは /tmp/history_feature_140a/prediction_core_candidate_files.txt に保存している。

この一覧は候補であり、すべてが prediction core 本体という意味ではない。

今後の接続前には、以下を分類する必要がある。

- prediction output generator
- dashboard compatibility patcher
- dashboard validator
- readiness checker
- documentation / static dashboard file
- actual score / recommendation calculation logic

## adapter 使用箇所

履歴特徴量 adapter 関連の使用箇所は、以下を中心に確認した。

- scripts/history_feature_prediction_adapter.py
- scripts/check_history_feature_prediction_adapter.py
- scripts/export_history_feature_adapter_preview.py
- scripts/check_history_feature_adapter_preview.py
- scripts/check_dashboard_history_feature_adapter_preview.py
- docs/index.html
- docs/prediction_history_feature_adapter_preview.json

現時点では、adapter は preview / diagnostics / readiness 用であり、prediction core には接続していない。

## racer_id / 選手 ID の接続観点

racer_id / racerId / player_id / playerId / registration_number / toban / 登番 を検索し、選手 ID の使用箇所を確認した。

今後 prediction core へ接続する場合は、以下が重要である。

- prediction 側の選手 ID キーを特定すること
- adapter 側の normalize / extract ロジックと一致させること
- ID が無い場合は default values を返すこと
- missing_candidate_count を監視すること
- ID 正規化により既存 prediction JSON 構造を壊さないこと

## config guard

history_feature_config.json、enabled:false、enabled:true、history_features_enabled などを検索した。

現時点の重要方針は以下である。

- top-level config は enabled:false
- enabled:false の間は prediction output を変更しない
- adapter preview は診断用に限定する
- enabled:true に進む前に additional audit を行う
- docs/prediction.json は無断で更新しない

## 重要な既存仕様

STEP139-A/B で確認した通り、scripts/check_dashboard_readiness_outputs_ready.py は内部で scripts/ensure_prediction_json_dashboard_compat.py を実行する。

ensure_prediction_json_dashboard_compat.py は、docs/prediction.json に dashboard 表示互換用フィールドを補正することがある。

そのため、no-change audit では以下が必要である。

- 実行前後の hash 比較
- git diff 確認
- docs/prediction.json が modified になった場合の git restore
- dashboard compatibility 補正と prediction core 変更の区別

## 最小接続候補の考え方

履歴特徴量を prediction core に接続する場合の最小変更方針は以下である。

1. prediction output generator を特定する
2. score / recommendation 計算直前の入力データ構造を特定する
3. racer_id を抽出する
4. history_feature_prediction_adapter.py から履歴特徴量を取得する
5. enabled:false の間は prediction score に反映しない
6. まず shadow / dry-run fields として出力する
7. A/B preview と adapter preview の差分を確認する
8. enabled:true 化前に rollback tag を確認する

## まだ実施しないこと

現時点では以下を実施しない。

- enabled:true
- score 加算
- rank 変更
- recommendation 並び替え
- expected_value 変更
- docs/prediction.json の構造変更
- production prediction core への直接接続

## 関連 stable tag

現在の安全状態に関連する tag は以下である。

- history-feature-ab-preview-stable
- history-feature-pre-enable-audit-stable
- history-feature-adapter-dry-run-stable
- history-feature-adapter-preview-dashboard-stable
- history-feature-final-diff-audit-stable

## 結論

STEP140-A により、prediction core 接続候補の調査ログを作成した。

現時点では、履歴特徴量は prediction core に接続していない。

次のステップでは、この調査結果をもとに、prediction core への最小安全接続案を設計する。
