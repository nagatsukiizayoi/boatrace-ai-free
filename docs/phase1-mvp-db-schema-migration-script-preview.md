# Phase 1 MVP DB schema migration script preview 記録

## 概要

この文書は、STEP153-A から STEP153-D までで実施した Phase 1 MVP DB schema migration script preview の内容を記録するものです。

本ステップは、将来 migration script を作成する前に、その設計方針と安全条件を preview として記録するものです。

この段階では、migration script は作成しません。

また、実際の db/schema.sql 変更、db/boatrace.sqlite3 変更、CREATE TABLE 実行、ALTER TABLE 実行、DROP TABLE 実行、INSERT / UPDATE / DELETE 実行、migration 実行、prediction core 接続、予測出力変更は行いません。

## 対象 preview

- step: STEP153-B
- preview_type=phase1-mvp-db-schema-migration-script-preview
- connection_mode=migration-preview-only
- migration_script_preview_only:true
- migration_script_execution_mode=not-created-not-executed
- ddl_execution_mode=not-executed
- safe_mode:true

## STEP153-A: migration script feasibility audit with PDF final design compatibility

STEP153-A では、migration script feasibility audit を実施しました。

添付 PDF の最終設計を反映し、以下を確認しました。

- Phase 1 MVP 8テーブルと PDF 最終DB設計の対応
- PDF にある追加テーブルの deferred 扱い
- race_id = canonical_race_key 方針
- canonical_candidate_key = race_id + "_" + lane 方針
- PRE_NIGHT / MORNING / POST_EXHIBITION / FINAL の段階導入方針
- live JSON から nightly SQLite merge する方針
- no automatic betting
- 5 to 15 minutes collection interval
- LLM not used for normal prediction
- 既存 history_races / history_results の preserve 方針
- DDL preview が add-only であること
- CREATE TABLE IF NOT EXISTS 方針であること
- DROP TABLE / destructive ALTER / DELETE / UPDATE を使わないこと

STEP153-A は audit-only であり、repository file は変更していません。

## STEP153-B: migration script preview exporter / JSON

STEP153-B では、migration script preview exporter を作成し、migration script preview JSON を出力しました。

- exporter: scripts/export_phase1_mvp_db_schema_migration_script_preview.py
- preview JSON: docs/phase1_mvp_db_schema_migration_script_preview.json

出力された preview JSON は以下の安全設定を持ちます。

- preview_type=phase1-mvp-db-schema-migration-script-preview
- connection_mode=migration-preview-only
- migration_script_preview_only:true
- migration_script_execution_mode=not-created-not-executed
- ddl_execution_mode=not-executed
- creates_migration_script:false
- runs_migration:false
- executes_ddl:false
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- drops_tables:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false
- minimal_table_count=8

## STEP153-C: migration script preview checker

STEP153-C では、migration script preview JSON を検証する checker を作成しました。

- checker: scripts/check_phase1_mvp_db_schema_migration_script_preview.py

checker は以下を確認します。

- step=STEP153-B
- preview_type=phase1-mvp-db-schema-migration-script-preview
- connection_mode=migration-preview-only
- migration_script_preview_only:true
- migration_script_execution_mode=not-created-not-executed
- ddl_execution_mode=not-executed
- creates_migration_script:false
- runs_migration:false
- executes_ddl:false
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- drops_tables:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false
- minimal_table_count=8
- race_id = canonical_race_key
- canonical_candidate_key = race_id + "_" + lane
- PDF final design compatibility
- deferred final design tables
- no automatic betting
- collection interval policy: 5 to 15 minutes
- sqlite commit policy: nightly SQLite merge
- LLM not used for normal prediction
- history_races / history_results preserve
- PRE_NIGHT constraints
- db/schema.sql に未コミット差分がないこと
- db/boatrace.sqlite3 に未コミット差分がないこと
- docs/prediction.json に未コミット差分がないこと
- data/history_feature_config.json に未コミット差分がないこと
- docs/phase1_mvp_db_schema_migration_script_preview.json に未コミット差分がないこと
- docs/phase1_mvp_db_schema_ddl_preview.json に未コミット差分がないこと

代表的な確認済み出力:

- Phase 1 MVP DB schema migration script preview validation: OK
- STEP 153-C CHECK: OK

## STEP153-D: readiness 登録

STEP153-D では、STEP153-C の checker を readiness checks に登録しました。

変更対象は以下の 2 ファイルのみです。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録された checker:

- scripts/check_phase1_mvp_db_schema_migration_script_preview.py

登録された required JSON:

- docs/phase1_mvp_db_schema_migration_script_preview.json

readiness 実行時には、以下の OK が確認されます。

- STEP 153-C CHECK: OK
- STEP 152-C CHECK: OK
- STEP 151-C CHECK: OK
- STEP 150-C CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## Minimal table count

Phase 1 MVP DB schema の minimal_table_count=8 です。

対象テーブルは以下です。

1. races
2. entries
3. feature_sets
4. prediction_runs
5. predictions
6. results
7. payouts
8. stage_metrics

## Migration script design direction

将来 migration script を作成する場合の方針は以下です。

- add-only
- idempotent
- guarded by safety checks
- CREATE TABLE IF NOT EXISTS
- requires pre-migration hash record
- requires SQLite backup before execution
- DROP TABLE 禁止
- DROP INDEX 禁止
- destructive ALTER TABLE 禁止
- history tables への DELETE 禁止
- history tables への UPDATE 禁止
- REPLACE INTO history tables 禁止

ただし、STEP153-E 時点では migration script は作成しません。

## Key policy

STEP149 からの canonical key policy を継続します。

PDF 最終設計との compatibility decision として、Phase 1 MVP では以下を採用します。

- race_id = canonical_race_key
- canonical_candidate_key = race_id + "_" + lane

canonical_race_key:

- canonical_race_key = race_date + "_" + venue_id + "_" + race_no

components:

- race_date
- venue_id
- race_no

canonical_candidate_key:

- canonical_candidate_key = race_date + "_" + venue_id + "_" + race_no + "_" + lane

components:

- race_date
- venue_id
- race_no
- lane

## PDF final design compatibility

添付 PDF の最終設計は、Phase 1 MVP より広いシステム全体設計です。

現在の Phase 1 MVP は、その安全な subset として扱います。

Phase 1 MVP で対象とする table:

- races
- entries
- feature_sets
- prediction_runs
- predictions
- results
- payouts
- stage_metrics

## Deferred final design tables

以下は PDF 最終設計に含まれますが、Phase 1 MVP では deferred とします。

- racer_stats_snapshot
- motor_boat_stats_snapshot
- venue_bias_daily
- weather_water_snapshots
- exhibition_snapshots
- odds_snapshots
- ingestion_runs
- prediction_changes
- stage_transition_metrics
- model_registry
- training_runs

これらは忘れているのではなく、Phase 2 以降に段階導入します。

## Phase mapping

### Phase 1

- PRE_NIGHT prediction
- PRE_NIGHT evaluation
- minimal DB schema
- races / entries / feature_sets / prediction_runs / predictions / results / payouts / stage_metrics

### Phase 2

- MORNING update
- weather_water_snapshots

### Phase 3

- POST_EXHIBITION update
- exhibition_snapshots

### Phase 4

- odds_snapshots
- expected value
- FINAL stage
- prediction_changes

### Phase 5

- stage_transition_metrics
- model_registry
- training_runs
- LLM weekly evaluation analysis

## PDF operation constraints

添付 PDF の運用制約として、以下を維持します。

- no automatic betting
- collection interval policy: 5 to 15 minutes
- avoid high-frequency fetching
- cache fetched data
- fallback on failure
- intraday updates: JSON-centered updates
- sqlite commit policy: nightly SQLite merge
- LLM not used for normal prediction
- LLM allowed scope: weekly evaluation analysis only
- smartphone operation supported

## Existing history tables policy

既存 history tables は preserve します。

対象:

- history_races
- history_results

方針:

- drop しない
- recreate しない
- destructive alter しない
- delete しない
- update しない
- 既存 row を削除しない
- 既存履歴 DB を破壊しない

## PRE_NIGHT constraints

PRE_NIGHT 予測では、予測時点で未知の情報を input として使いません。

使用禁止の代表例:

- same-day odds
- final odds
- exhibition data
- exhibition_time
- exhibition ST
- exhibition course
- same-day weather
- same-day water condition
- results
- payouts
- confirmed race outcome
- post-race information

results / payouts は、race 後の training label / evaluation 用としては扱えますが、PRE_NIGHT input としては使用しません。

## Rollback requirements for future migration

将来 migration を実行する場合は、事前に以下を記録します。

- git status
- git hash
- sha256 of db/schema.sql
- sha256 of db/boatrace.sqlite3
- sha256 of docs/prediction.json
- sha256 of data/history_feature_config.json
- existing sqlite table list
- history_races row count
- history_results row count
- SQLite backup before execution

ただし、STEP153-E 時点では migration は実行しません。

## 変更していないファイル

STEP153-E では以下のファイルを変更しません。

- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/phase1_mvp_db_schema_migration_script_preview.json
- docs/phase1_mvp_db_schema_ddl_preview.json
- docs/phase1_mvp_db_schema_preview.json
- docs/phase1_mvp_db_schema_implementation_plan_preview.json
- scripts/export_phase1_mvp_db_schema_migration_script_preview.py
- scripts/check_phase1_mvp_db_schema_migration_script_preview.py

## 禁止事項

STEP153-E では以下を行いません。

- db/schema.sql の変更
- db/boatrace.sqlite3 の変更
- CREATE TABLE 実行
- ALTER TABLE 実行
- DROP TABLE 実行
- INSERT / UPDATE / DELETE 実行
- migration script 作成
- migration 実行
- executes_ddl:true への変更
- creates_migration_script:true への変更
- history feature 有効化
- prediction core 接続
- docs/prediction.json の変更
- preview JSON の変更
- scripts の変更
- dashboard UI 追加
- prediction score / rank / recommendation / expected value の変更

## Readiness check status

STEP153-D までに readiness 登録済みです。

期待される OK line:

- STEP 153-C CHECK: OK
- STEP 152-C CHECK: OK
- STEP 151-C CHECK: OK
- STEP 150-C CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## 現在の状態

現時点では、Phase 1 MVP DB schema migration script は preview-only です。

- migration_script_preview_only:true
- migration_script_execution_mode=not-created-not-executed
- ddl_execution_mode=not-executed
- creates_migration_script:false
- runs_migration:false
- executes_ddl:false
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- drops_tables:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false

## 次ステップ

STEP153-E 完了後は、STEP153-F で stable tag を作成します。

STEP153-F では file modification は行わず、現在の safe migration script preview state に tag を付与します。
