# Phase 1 MVP DB schema migration draft 記録

## 概要

この記録は STEP154-B 〜 STEP154-D で作成・検証・readiness 登録した Phase 1 MVP DB schema migration draft の状態を文書化する。

この STEP154-E は documentation-only の工程であり、以下は実施しない。

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

## 対象 draft

- step: STEP154-B
- draft script: scripts/migrate_phase1_mvp_db_schema.py
- checker: scripts/check_phase1_mvp_db_schema_migration_draft.py
- readiness registration: STEP154-D
- mode=dry-run
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- minimal_table_count=8

## STEP154-B: migration draft script 作成

STEP154-B では scripts/migrate_phase1_mvp_db_schema.py を作成した。

この script は migration を実行しない。
DDL 候補を dry-run preview として保持・表示するだけであり、DB 変更は行わない。

### STEP154-B expected output

- Phase 1 MVP DB schema migration draft: OK
- STEP 154-B CHECK: OK
- mode=dry-run
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- minimal_table_count=8
- danger_pattern_count=0
- danger_patterns=NONE

## STEP154-C: migration draft checker 作成

STEP154-C では scripts/check_phase1_mvp_db_schema_migration_draft.py を作成した。

checker は以下を検証する。

- draft script が存在すること
- draft script が dry-run であること
- DDL を実行しないこと
- DB に書き込まないこと
- db/schema.sql に書き込まないこと
- docs/prediction.json を変更しないこと
- data/history_feature_config.json を有効化しないこと
- minimal_table_count=8
- DDL 候補が CREATE TABLE IF NOT EXISTS を含むこと
- DDL 候補に危険語が含まれないこと
- preview JSON と key policy が整合していること
- PDF 反映制約が保持されていること
- 禁止ファイルに未コミット差分が無いこと

### STEP154-C expected output

- Phase 1 MVP DB schema migration draft validation: OK
- STEP 154-C CHECK: OK
- mode=dry-run
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- minimal_table_count=8
- danger_pattern_count=0
- danger_patterns=NONE
- race_id_policy=race_id = canonical_race_key
- canonical_candidate_key_policy=canonical_candidate_key = race_id + "_" + lane
- schema_sql_currently_modified=False
- database_currently_modified=False
- prediction_json_currently_modified=False
- config_currently_modified=False
- migration_preview_currently_modified=False
- ddl_preview_currently_modified=False

## STEP154-D: readiness 登録

STEP154-D では以下の readiness script に checker を登録した。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録された checker:

- scripts/check_phase1_mvp_db_schema_migration_draft.py

関連 required file:

- scripts/migrate_phase1_mvp_db_schema.py

### STEP154-D readiness expected output

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

## DDL draft policy

STEP154-B の draft script は DDL 候補文字列を保持するが、実行しない。

許可される設計方針:

- dry-run only
- preview only
- add-only
- idempotent
- CREATE TABLE IF NOT EXISTS 文字列のみ
- future migration では事前 backup 必須
- existing history tables を preserve

禁止される操作:

- DROP TABLE
- DROP INDEX
- ALTER TABLE
- INSERT INTO
- UPDATE
- DELETE FROM
- REPLACE INTO
- TRUNCATE
- destructive migration
- DB write
- schema.sql write

補足:

- DANGER_PATTERNS に危険語文字列が定義されていること自体は検査用であり OK。
- 実際の DDL 候補 DDL_CANDIDATES の中に危険語が含まれないことを checker が検証する。

## Key policy

Phase 1 MVP では PDF 最終設計との整合性のため、以下の key 方針を採用する。

- race_id = canonical_race_key
- canonical_race_key = race_date + "_" + venue_id + "_" + race_no
- canonical_candidate_key = race_id + "_" + lane

これにより、PDF 側の race_id と、現行 preview chain の canonical key 方針を同義として扱う。

## PDF 反映制約

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

## Files unchanged in STEP154-E

STEP154-E では以下を変更しない。

- scripts/migrate_phase1_mvp_db_schema.py
- scripts/check_phase1_mvp_db_schema_migration_draft.py
- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py
- scripts/export_phase1_mvp_db_schema_migration_script_preview.py
- scripts/check_phase1_mvp_db_schema_migration_script_preview.py
- docs/phase1_mvp_db_schema_migration_script_preview.json
- docs/phase1_mvp_db_schema_ddl_preview.json
- docs/phase1_mvp_db_schema_implementation_plan_preview.json
- docs/phase1_mvp_db_schema_preview.json
- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json

## Safety status

現在の安全状態:

- mode=dry-run
- executes_ddl=False
- writes_database=False
- writes_schema_sql=False
- creates_tables=False
- alters_tables=False
- drops_tables=False
- runs_migration=False
- minimal_table_count=8
- danger_pattern_count=0
- danger_patterns=NONE
- config_enabled=False
- history_features_enabled=False
- prediction_core_connected=False

## Completion criteria

STEP154-E の完了条件:

- this Markdown exists
- README link exists
- migration draft dry-run status documented
- no DDL execution documented
- no DB/schema/prediction/config modification documented
- STEP 154-C CHECK: OK documented
- minimal_table_count=8 documented
- key policy documented
- PDF constraints documented
- prohibited file diffs are empty
- changed files are only README.md and this Markdown

## Next step

次は STEP154-F で stable tag を作成する。

STEP154-F ではファイル変更を行わない。
