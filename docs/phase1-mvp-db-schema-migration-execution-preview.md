# Phase 1 MVP DB schema migration execution preview 記録

## 概要

この記録は STEP155-B 〜 STEP155-D で作成・検証・readiness 登録した Phase 1 MVP DB schema migration execution preview の状態を文書化する。

この STEP155-E は documentation-only の工程であり、以下は実施しない。

- migration 実行
- DDL 実行
- CREATE TABLE 実行
- ALTER TABLE 実行
- DROP TABLE 実行
- INSERT / UPDATE / DELETE 実行
- db/schema.sql 変更
- db/boatrace.sqlite3 変更
- docs/prediction.json 変更
- data/history_feature_config.json 変更
- prediction core 接続
- history feature 有効化
- scripts/export_phase1_mvp_db_schema_migration_execution_preview.py 変更
- scripts/check_phase1_mvp_db_schema_migration_execution_preview.py 変更
- docs/phase1_mvp_db_schema_migration_execution_preview.json 変更

## 対象 preview

- step: STEP155-B
- exporter: scripts/export_phase1_mvp_db_schema_migration_execution_preview.py
- preview JSON: docs/phase1_mvp_db_schema_migration_execution_preview.json
- checker: scripts/check_phase1_mvp_db_schema_migration_execution_preview.py
- readiness registration: STEP155-D
- preview_type=phase1-mvp-db-schema-migration-execution-preview
- connection_mode=execution-preview-only
- execution_preview_only=True
- migration_execution_mode=not-executed
- ddl_execution_mode=not-executed
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- modifies_prediction_json=False
- writes_prediction_json=False
- prediction_core_connected=False
- config_enabled=False
- history_features_enabled=False
- minimal_table_count=8

## STEP155-B: execution preview exporter 作成

STEP155-B では scripts/export_phase1_mvp_db_schema_migration_execution_preview.py を作成した。

この exporter は execution preview JSON を生成するだけであり、migration を実行しない。
DDL も実行しない。
DB/schema/prediction/config は変更しない。

生成ファイル:

- docs/phase1_mvp_db_schema_migration_execution_preview.json

### STEP155-B expected output

- Phase 1 MVP DB schema migration execution preview export: OK
- STEP 155-B CHECK: OK
- preview_type=phase1-mvp-db-schema-migration-execution-preview
- connection_mode=execution-preview-only
- execution_preview_only=True
- migration_execution_mode=not-executed
- ddl_execution_mode=not-executed
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- modifies_prediction_json=False
- writes_prediction_json=False
- prediction_core_connected=False
- config_enabled=False
- history_features_enabled=False
- minimal_table_count=8
- draft_script=scripts/migrate_phase1_mvp_db_schema.py
- draft_mode=dry-run
- ddl_candidates_table_count=8
- ddl_candidates_danger_pattern_count=0

## STEP155-C: execution preview checker 作成

STEP155-C では scripts/check_phase1_mvp_db_schema_migration_execution_preview.py を作成した。

checker は以下を検証する。

- preview JSON が存在すること
- step=STEP155-B
- preview_type=phase1-mvp-db-schema-migration-execution-preview
- connection_mode=execution-preview-only
- safe_mode=True
- execution_preview_only=True
- migration_execution_mode=not-executed
- ddl_execution_mode=not-executed
- all execution/write flags are False
- minimal_table_count=8
- draft_mode=dry-run
- ddl_candidates_table_count=8
- ddl_candidates_danger_pattern_count=0
- future execution requirements が安全条件を満たすこと
- forbidden SQL patterns が定義されていること
- rollback requirements が定義されていること
- key policy が整合していること
- PDF 反映制約が保持されていること
- PRE_NIGHT constraints が保持されていること
- 禁止ファイルに未コミット差分が無いこと

### STEP155-C expected output

- Phase 1 MVP DB schema migration execution preview validation: OK
- STEP 155-C CHECK: OK
- preview_type=phase1-mvp-db-schema-migration-execution-preview
- connection_mode=execution-preview-only
- execution_preview_only=True
- migration_execution_mode=not-executed
- ddl_execution_mode=not-executed
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- modifies_prediction_json=False
- writes_prediction_json=False
- prediction_core_connected=False
- config_enabled=False
- history_features_enabled=False
- minimal_table_count=8
- draft_mode=dry-run
- ddl_candidates_table_count=8
- ddl_candidates_danger_pattern_count=0
- race_id_policy=race_id = canonical_race_key
- canonical_candidate_key_policy=canonical_candidate_key = race_id + "_" + lane
- no_automatic_betting=True
- collection_interval_policy=5 to 15 minutes
- sqlite_commit_policy=nightly SQLite merge
- llm_usage_policy=LLM not used for normal prediction
- schema_sql_currently_modified=False
- database_currently_modified=False
- prediction_json_currently_modified=False
- config_currently_modified=False
- execution_preview_currently_modified=False

## STEP155-D: readiness 登録

STEP155-D では以下の readiness script に checker を登録した。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録された checker:

- scripts/check_phase1_mvp_db_schema_migration_execution_preview.py

関連 required file:

- docs/phase1_mvp_db_schema_migration_execution_preview.json

### STEP155-D readiness expected output

- STEP 155-C CHECK: OK
- STEP 154-C CHECK: OK
- STEP 153-C CHECK: OK
- STEP 152-C CHECK: OK
- STEP 151-C CHECK: OK
- STEP 150-C CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## Phase 1 MVP minimal tables

minimal_table_count=8

対象テーブル:

1. races
2. entries
3. feature_sets
4. prediction_runs
5. predictions
6. results
7. payouts
8. stage_metrics

## Future execution requirements

将来 execution mode を追加する場合でも、以下を満たす必要がある。

- explicit_execution_flag_required=True
- default_mode_must_remain_dry_run=True
- clean_git_status_required=True
- sqlite_backup_required=True
- protected_file_hash_record_required=True
- readiness_checks_required=True
- create_table_if_not_exists_only=True
- destructive_sql_forbidden=True
- preserve_history_tables=True
- prediction_json_write_forbidden=True
- config_enablement_forbidden=True
- prediction_core_connection_forbidden=True
- automatic_betting_forbidden=True
- execution_must_be_separate_explicit_step=True
- future_candidate_statement=CREATE TABLE IF NOT EXISTS

重要:

- execution mode は将来の明示的な別 STEP でのみ扱う。
- default は dry-run のままにする。
- STEP155-B/E では execution mode を実装しない。
- STEP155-B/E では migration を実行しない。

## Forbidden SQL patterns

将来 execution mode でも以下は禁止する。

- DROP TABLE
- DROP INDEX
- ALTER TABLE
- INSERT INTO
- UPDATE 
- DELETE FROM
- REPLACE INTO
- TRUNCATE

補足:

- UPDATE は updated_at の誤検知を避けるため、検査上は trailing space 付きの UPDATE  を使用する。
- DDL_CANDIDATES は CREATE TABLE IF NOT EXISTS のみを許可する。
- destructive SQL は禁止する。

## Rollback requirements

将来の実 execution 前には rollback 前提を満たす必要がある。

必須:

- backup db/boatrace.sqlite3
- record git status
- record commit hash
- record sha256 db/schema.sql
- record sha256 db/boatrace.sqlite3
- record sha256 docs/prediction.json
- record sha256 data/history_feature_config.json
- record SQLite table list
- record row counts
- run readiness checks

Rollback:

- restore SQLite backup
- git restore tracked files
- do not drop history_races
- do not drop history_results
- do not recreate existing history tables
- do not delete/update existing history records

## Key policy

Phase 1 MVP では PDF 最終設計との整合性のため、以下の key 方針を採用する。

- race_id = canonical_race_key
- canonical_race_key = race_date + "_" + venue_id + "_" + race_no
- canonical_candidate_key = race_id + "_" + lane

これにより、PDF 側の race_id と、現行 preview chain の canonical key 方針を同義として扱う。

## PDF operation constraints

PDF 最終設計を反映しつつ、Phase 1 MVP では安全な最小 subset のみを扱う。

運用制約:

- no automatic betting
- collection interval: 5 to 15 minutes
- sqlite commit policy: nightly SQLite merge
- llm usage policy: LLM not used for normal prediction
- smartphone-centric operation

Phase 1 MVP で defer する final design tables:

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

## Existing history tables policy

既存 history tables は preserve する。

- history_races
- history_results

禁止:

- drop
- recreate
- destructive alter
- delete/update existing history records

## PRE_NIGHT constraints

PRE_NIGHT 段階では、レース後または当日確定後の情報を事前予測入力として使用しない。

- pre_night_only=True
- results_and_payouts_allowed_as_pre_night_inputs=False

禁止情報:

- same-day odds
- final odds
- exhibition data
- exhibition_time
- same-day weather
- same-day water condition
- confirmed race outcome
- results
- payouts
- post-race information

results と payouts は将来 DB の保存対象候補ではあるが、PRE_NIGHT の予測入力としては使用しない。

## Files unchanged in STEP155-E

STEP155-E では以下を変更しない。

- scripts/export_phase1_mvp_db_schema_migration_execution_preview.py
- scripts/check_phase1_mvp_db_schema_migration_execution_preview.py
- docs/phase1_mvp_db_schema_migration_execution_preview.json
- scripts/migrate_phase1_mvp_db_schema.py
- scripts/check_phase1_mvp_db_schema_migration_draft.py
- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/*.json
- scripts/*.py

## Safety status

現在の安全状態:

- execution_preview_only=True
- migration_execution_mode=not-executed
- ddl_execution_mode=not-executed
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- modifies_prediction_json=False
- writes_prediction_json=False
- prediction_core_connected=False
- config_enabled=False
- history_features_enabled=False
- minimal_table_count=8

## Completion criteria

STEP155-E の完了条件:

- this Markdown exists
- README link exists
- execution preview status documented
- migration_execution_mode=not-executed documented
- ddl_execution_mode=not-executed documented
- executes_ddl=False documented
- writes_database=False documented
- writes_schema_sql=False documented
- STEP 155-C CHECK: OK documented
- future execution requirements documented
- forbidden SQL documented
- rollback requirements documented
- key policy documented
- PDF constraints documented
- PRE_NIGHT constraints documented
- prohibited file diffs are empty
- changed files are only README.md and this Markdown

## Next step

次は STEP155-F で stable tag を作成する。

STEP155-F ではファイル変更を行わない。
