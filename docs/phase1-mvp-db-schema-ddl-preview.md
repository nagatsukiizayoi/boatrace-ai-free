# Phase 1 MVP DB schema DDL preview 記録

## 概要

この文書は、STEP152-A から STEP152-D までで実施した Phase 1 MVP DB schema DDL preview の内容を記録するものです。

本ステップは、Phase 1 MVP DB schema の将来 DDL を確認するための preview-only 記録です。

この段階では、実際の db/schema.sql 変更、db/boatrace.sqlite3 変更、CREATE TABLE 実行、ALTER TABLE 実行、DROP TABLE 実行、migration 実行、prediction core 接続、予測出力変更は行いません。

## 対象 preview

- step: STEP152-B
- preview_type: phase1-mvp-db-schema-ddl-preview
- connection_mode: ddl-preview-only
- ddl_execution_mode=not-executed
- ddl_preview_only:true
- safe_mode:true

## STEP152-A: DDL feasibility audit

STEP152-A では、Phase 1 MVP DB schema DDL feasibility audit を実施しました。

確認した主な内容は以下です。

- db/schema.sql の存在確認
- db/schema.sql 内の CREATE TABLE 記述確認
- db/boatrace.sqlite3 の既存 table 確認
- history_races の存在確認
- history_results の存在確認
- Phase 1 MVP minimal tables の gap analysis
- add-only 方針
- PRE_NIGHT constraints
- db/schema.sql が変更されていないこと
- db/boatrace.sqlite3 が変更されていないこと
- docs/prediction.json が変更されていないこと
- data/history_feature_config.json が変更されていないこと

STEP152-A は audit-only であり、DDL 実行や DB 変更は行っていません。

## STEP152-B: DDL preview exporter / JSON

STEP152-B では、Phase 1 MVP DB schema DDL preview exporter を作成し、DDL preview JSON を出力しました。

- exporter: scripts/export_phase1_mvp_db_schema_ddl_preview.py
- preview JSON: docs/phase1_mvp_db_schema_ddl_preview.json

出力された preview JSON は以下の安全設定を持ちます。

- preview_type=phase1-mvp-db-schema-ddl-preview
- connection_mode=ddl-preview-only
- ddl_execution_mode=not-executed
- ddl_preview_only:true
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- drops_tables:false
- runs_migration:false
- executes_ddl:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false

## STEP152-C: DDL preview checker

STEP152-C では、DDL preview JSON を検証する checker を作成しました。

- checker: scripts/check_phase1_mvp_db_schema_ddl_preview.py

checker は以下を確認します。

- step=STEP152-B
- preview_type=phase1-mvp-db-schema-ddl-preview
- connection_mode=ddl-preview-only
- ddl_execution_mode=not-executed
- ddl_preview_only:true
- safe_mode:true
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- drops_tables:false
- runs_migration:false
- executes_ddl:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false
- minimal_table_count=8
- DDL direction が add-only であること
- future_candidate_statement が CREATE TABLE IF NOT EXISTS であること
- history_races / history_results が preserve 方針であること
- PRE_NIGHT constraints が記録されていること
- db/schema.sql に未コミット差分がないこと
- db/boatrace.sqlite3 に未コミット差分がないこと
- docs/prediction.json に未コミット差分がないこと
- data/history_feature_config.json に未コミット差分がないこと

代表的な確認済み出力:

- Phase 1 MVP DB schema DDL preview validation: OK
- STEP 152-C CHECK: OK

## STEP152-D: readiness 登録

STEP152-D では、STEP152-C の checker を readiness checks に登録しました。

変更対象は以下の 2 ファイルのみです。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録された checker:

- scripts/check_phase1_mvp_db_schema_ddl_preview.py

登録された required JSON:

- docs/phase1_mvp_db_schema_ddl_preview.json

readiness 実行時には、以下の OK が確認されます。

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

## DDL direction

DDL preview の方針は add-only です。

将来候補となる DDL の基本方針:

- CREATE TABLE IF NOT EXISTS
- DROP TABLE 禁止
- 破壊的 ALTER TABLE 禁止
- migration はこの step では実行しない
- db/schema.sql はこの step では変更しない
- db/boatrace.sqlite3 はこの step では変更しない

STEP152-B / STEP152-C / STEP152-D / STEP152-E の段階では、DDL は preview であり、実行されません。

## Canonical key policy

STEP149 で決定した canonical key policy を継続します。

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

## Phase 1 MVP tables

Phase 1 MVP DDL preview は以下の table を対象とします。

### races

Race-level master table。

Primary key candidate:

- canonical_race_key

### entries

Lane / candidate-level entry table。

Primary key candidate:

- canonical_candidate_key

### feature_sets

PRE_NIGHT-safe feature snapshot metadata table。

Primary key candidate:

- feature_set_id

### prediction_runs

Prediction run metadata table。

Primary key candidate:

- prediction_run_id

### predictions

Candidate-level prediction archive table。

Primary key candidate:

- prediction_id

### results

Post-race result table。

PRE_NIGHT input としては使用しません。

Primary key candidate:

- canonical_race_key

### payouts

Post-race payout table。

PRE_NIGHT input としては使用しません。

Primary key candidate:

- canonical_race_key

### stage_metrics

Stage-level metrics / monitoring table。

Primary key candidate:

- stage_metric_id

## Existing history tables policy

既存 history tables は preserve します。

対象:

- history_races
- history_results

方針:

- drop しない
- recreate しない
- destructive alter しない
- 既存 row を削除しない
- 既存履歴 DB を破壊しない

## PRE_NIGHT constraints

PRE_NIGHT 予測では、予測時点で未知の情報を input として使いません。

使用禁止の代表例:

- same-day odds
- final odds
- exhibition data
- exhibition_time
- same-day weather
- same-day water condition
- results
- payouts
- confirmed race outcome
- post-race information

results / payouts は、race 後の training label / evaluation 用としては扱えますが、PRE_NIGHT input としては使用しません。

## 変更していないファイル

STEP152-E では以下のファイルを変更しません。

- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/phase1_mvp_db_schema_ddl_preview.json
- docs/phase1_mvp_db_schema_preview.json
- docs/phase1_mvp_db_schema_implementation_plan_preview.json
- scripts/export_phase1_mvp_db_schema_ddl_preview.py
- scripts/check_phase1_mvp_db_schema_ddl_preview.py

## 禁止事項

STEP152-E では以下を行いません。

- db/schema.sql の変更
- db/boatrace.sqlite3 の変更
- CREATE TABLE 実行
- ALTER TABLE 実行
- DROP TABLE 実行
- migration 実行
- executes_ddl:true への変更
- history feature 有効化
- prediction core 接続
- docs/prediction.json の変更
- preview JSON の変更
- scripts の変更
- dashboard UI 追加
- prediction score / rank / recommendation / expected value の変更

## Readiness check status

STEP152-D までに readiness 登録済みです。

期待される OK line:

- STEP 152-C CHECK: OK
- STEP 151-C CHECK: OK
- STEP 150-C CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## 現在の状態

現時点では、Phase 1 MVP DB schema DDL は preview-only です。

- ddl_execution_mode=not-executed
- ddl_preview_only:true
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- drops_tables:false
- runs_migration:false
- executes_ddl:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false

## 次ステップ

STEP152-E 完了後は、STEP152-F で stable tag を作成します。

STEP152-F では file modification は行わず、現在の safe DDL preview state に tag を付与します。
