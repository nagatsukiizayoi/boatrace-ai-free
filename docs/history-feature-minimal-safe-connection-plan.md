# 履歴特徴量 minimal safe connection plan

## 概要

本ドキュメントは、履歴特徴量を prediction core に接続する前に作成した minimal safe connection plan の記録です。

STEP145-A では、これまでの監査結果を踏まえ、最初の実装方針を shadow-only isolated path とすることを決定しました。

この段階では prediction core への接続は行っていません。

enabled:true への変更も行っていません。

docs/prediction.json、予測スコア、順位、推奨買い目、期待値も変更していません。

## 対象ステップ

- STEP145-A: minimal safe connection planning
- STEP145-B: minimal safe connection plan ドキュメント化

## 参照した監査結果

本計画は以下の結果を踏まえています。

- pre-enable safety audit
- prediction core connection point audit
- prediction writer final identification
- shadow preview dashboard integration
- readiness checks

関連ドキュメント:

- docs/history-feature-pre-enable-safety-audit.md
- docs/history-feature-prediction-core-connection-point-audit.md
- docs/history-feature-prediction-writer-final-identification.md
- docs/history-feature-shadow-preview-dashboard-completion.md

## 現在の安全状態

data/history_feature_config.json は enabled:false を維持しています。

docs/prediction.json は未変更です。

prediction core は未変更です。

prediction output は unchanged です。

現在の方針:

shadow preview only
enabled:false
prediction output unchanged
prediction core unmodified

## high-risk writer decision

STEP144-A/B の結果から、以下を first target にしないことを決定しました。

- scripts/seed_sample_data.py

理由:

- 複数の generated docs JSON を更新する可能性がある
- HTML 生成物を更新する可能性がある
- db/schema.sql に影響する可能性がある
- data/import/google_sheets 以下を更新する可能性がある
- data/raw/google_sheets 以下に preview CSV を生成する可能性がある

そのため、scripts/seed_sample_data.py を最初の履歴特徴量接続先にすることは避けます。

## dashboard compatibility decision

以下も履歴特徴量の first connection point にはしません。

- scripts/ensure_prediction_json_dashboard_compat.py

理由:

- 既存 dashboard compatibility 補正用の script である
- docs/prediction.json を一時的に変更することがある
- 履歴特徴量の接続ポイントとして使うと、prediction output 差分の原因が分かりにくくなる

この script を実行して docs/prediction.json が変更された場合は、必ず git restore docs/prediction.json で戻します。

## minimal safe connection direction

最初の実装方針は以下です。

- shadow-only isolated path
- enabled:false を維持
- docs/prediction.json を変更しない
- prediction_final.json を変更しない
- generated output JSON を変更しない
- score を変更しない
- rank を変更しない
- recommendation を変更しない
- expected value を変更しない
- readiness checks で差分なしを確認する

## proposed first implementation target

最初の実装候補は、main prediction writer ではなく、独立した shadow-only script または dry-run path とします。

候補:

- scripts/history_feature_prediction_adapter.py
- scripts/export_history_feature_shadow_preview.py
- 新規の isolated dry-run script

この実装は、prediction candidates を読み取り、履歴特徴量診断情報を生成して、別 JSON にのみ出力します。

許可する出力先は preview JSON のみです。

禁止する出力先:

- docs/prediction.json
- docs/prediction_final.json
- docs/prediction_runs.json
- docs/evaluation.json
- db/schema.sql
- data/import/*
- data/raw/*

## config guard

今後の実装では必ず config guard を使用します。

必要条件:

- data/history_feature_config.json の enabled が false の場合、prediction output に影響しない
- default は no effect
- enabled:true は別ステップで明示的に扱う
- enabled:false のまま readiness が成功する

## required checks before implementation commit

実装を行う場合、commit 前に以下を確認します。

- python scripts/check_history_feature_config.py
- python scripts/check_history_feature_shadow_preview.py
- python scripts/check_dashboard_history_feature_shadow_preview.py
- python scripts/check_history_database_readiness.py
- python scripts/check_dashboard_readiness_outputs_ready.py
- git --no-pager diff -- docs/prediction.json が空であること
- git status が意図したファイルのみを示すこと

## rollback tags

rollback 可能な stable tag として以下を使用します。

- history-feature-shadow-preview-dashboard-stable
- history-feature-pre-enable-safety-audit-stable
- history-feature-prediction-core-connection-point-audit-stable
- history-feature-prediction-writer-final-identification-stable

## STEP145-A 結果

STEP145-A では以下を確認しました。

- prior audit key points reviewed
- CONFIG_ENABLED_FALSE_OK
- docs/prediction.json hash captured
- history feature connection candidate refs collected
- high-risk writer refs collected
- minimal safe connection plan created
- STEP 122 CHECK: OK
- STEP 141-B CHECK: OK
- STEP 141-E CHECK: OK
- docs/prediction.json diff confirmed empty
- final git status clean

## 変更していないもの

以下は変更していません。

- data/history_feature_config.json
- docs/prediction.json
- docs/prediction_history_feature_shadow_preview.json
- docs/prediction_history_feature_adapter_preview.json
- docs/index.html
- scripts/*.py
- db/schema.sql
- data/import/*
- data/raw/*
- prediction core
- 予測スコア
- 予測順位
- 推奨買い目
- 期待値

## 結論

履歴特徴量の first implementation は、main prediction writer ではなく、shadow-only isolated path とします。

現時点ではまだ prediction core 接続は行いません。

現在の状態は以下です。

shadow preview only
enabled:false
prediction output unchanged
prediction core unmodified

以上により、minimal safe connection plan の記録を完了します。
