# 履歴特徴量 prediction writer 最終特定 記録

## 概要

本ドキュメントは、履歴特徴量を prediction core に接続する前に実施した prediction writer / generator 最終特定の記録です。

STEP143-A では prediction core 接続ポイント候補を広く調査しました。

STEP144-A では、その候補の中から実際に docs/prediction.json や関連する予測生成物に影響する可能性がある writer / generator を再確認しました。

この段階では prediction core への接続は行っていません。

enabled:true への変更も行っていません。

docs/prediction.json、予測スコア、順位、推奨買い目、期待値も変更していません。

## 対象ステップ

- STEP144-A: prediction writer / generator 最終特定
- STEP144-B: prediction writer / generator 最終特定結果ドキュメント化

## 監査ログ

監査ログは以下に保存しました。

/tmp/history_feature_144a/

主なログ:

- prediction_writer_candidates_from_143a.txt
- prediction_writer_detailed_refs.txt
- modifier_detection.log
- history_adapter_function_refs.txt
- config_enabled_check.txt
- prediction_json_sha256_final.txt
- git_status_final.txt
- prediction_writer_final_identification_summary.txt
- git_status_dirty_before_restore.txt
- git_diff_stat_dirty_before_restore.txt

## prediction writer candidates

STEP143-A のログが /tmp から消えていたため、STEP144-A では prediction writer candidates を再生成しました。

再生成結果は以下に保存しました。

/tmp/history_feature_144a/prediction_writer_candidates_from_143a.txt

## detailed refs

docs/prediction.json、prediction_final.json、write_text、json.dump、open prediction などの参照を検索しました。

結果は以下に保存しました。

/tmp/history_feature_144a/prediction_writer_detailed_refs.txt

## modifier detection

候補スクリプトを実験的に実行し、docs/prediction.json や関連生成物への影響を確認しました。

結果は以下に保存しました。

/tmp/history_feature_144a/modifier_detection.log

この検出では、候補スクリプトの一部が docs/prediction.json だけでなく、複数の生成物やデータファイルを更新する可能性があることを確認しました。

## dirty working tree の検出

候補スクリプト実行後、git status --short により dirty working tree を検出しました。

例として以下のようなファイル変更が確認されました。

- data/import/google_sheets/google_sheets_history_profile.json
- db/schema.sql
- docs/bet_results_summary.json
- docs/bet_results_summary_history.json
- docs/evaluation.html
- docs/evaluation.json
- docs/evaluation_history.json
- docs/prediction_final.json
- docs/prediction_history_feature_adapter_preview.json
- docs/prediction_run_summary.json
- docs/prediction_runs.json
- docs/stage_evaluation.html
- docs/stage_evaluation.json
- docs/stage_evaluation_history.json
- docs/stage_history.html
- docs/stage_insights.html
- docs/stage_insights.json
- data/raw/google_sheets/*_preview.csv

これらは STEP144-A の調査中に生成または更新された可能性があるため、コミットしていません。

## restore 対応

dirty working tree 検出後、以下で tracked file の変更を戻しました。

git restore .

また、untracked の preview CSV を削除しました。

rm -f data/raw/google_sheets/google_sheet_*_preview.csv

最終的に git status が clean であることを確認しました。

## 重要な候補

特に注意が必要な候補として以下があります。

- scripts/seed_sample_data.py
- scripts/ensure_prediction_json_dashboard_compat.py

scripts/seed_sample_data.py は複数の docs JSON、HTML、db/schema.sql、google sheets 関連データに影響する可能性があります。

scripts/ensure_prediction_json_dashboard_compat.py は既存の dashboard compatibility 補正として docs/prediction.json を一時的に変更することがあります。

## history adapter function refs

履歴特徴量 adapter / shadow preview 関連の重要関数や count 項目を確認しました。

結果は以下に保存しました。

/tmp/history_feature_144a/history_adapter_function_refs.txt

確認対象:

- load_config
- enabled
- candidate_count
- matched_candidate_count
- missing_candidate_count
- history adapter related functions

## config 状態

data/history_feature_config.json は enabled:false を維持しています。

確認結果:

CONFIG_ENABLED_FALSE_OK

## docs/prediction.json の確認

docs/prediction.json は最終的に未変更です。

candidate script 実行中に変更が発生した場合でも、git restore により戻しました。

最終状態では docs/prediction.json の変更はコミットしていません。

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

## 安全方針

今回の監査時点では以下を維持しています。

- enabled:false
- prediction core 未接続
- docs/prediction.json 未変更
- generated prediction outputs not committed
- prediction output unchanged
- shadow preview only
- score / rank / recommendation / expected value unchanged

## 次の段階に進む前の注意

prediction core へ接続する前に、以下を再確認します。

- scripts/seed_sample_data.py を直接接続対象にするか慎重に判断すること
- 複数生成物を更新する script は dry-run または isolated mode が必要であること
- docs/prediction.json への差分を出さない guard が必要であること
- enabled:false の状態で prediction output が変わらないこと
- rollback 可能な stable tag が存在すること

## 結論

STEP144-A により、prediction writer / generator 候補の最終特定を進め、候補スクリプトの一部が複数の生成物を更新する可能性があることを確認しました。

そのため、prediction core 接続時には、直接 writer を変更する前に、より限定された dry-run / shadow path で接続する必要があります。

現時点では以下の状態です。

shadow preview only
enabled:false
prediction output unchanged
prediction core unmodified

以上により、prediction writer 最終特定の記録を完了します。
