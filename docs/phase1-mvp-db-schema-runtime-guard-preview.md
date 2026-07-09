# Phase 1 MVP DB schema runtime guard preview 記録

## 概要

この文書は STEP156-B 〜 STEP156-D で作成・検証・readiness 登録した **Phase 1 MVP DB schema runtime guard preview** の状態を記録する。

STEP156-E は documentation-only であり、以下は一切行わない。

- migration 実行
- DDL 実行
- CREATE TABLE 実行
- ALTER TABLE 実行
- DROP TABLE 実行
- INSERT / UPDATE / DELETE / REPLACE / TRUNCATE 実行
- `db/schema.sql` 変更
- `db/boatrace.sqlite3` 変更
- `docs/prediction.json` 変更
- `data/history_feature_config.json` 変更
- preview JSON 変更
- checker / exporter / readiness script 変更
- history feature enablement
- prediction core connection
- automatic betting

この文書は runtime guard preview の安全条件・将来実行時の前提・rollback policy を記録するためのものであり、実際の DB migration を許可または実行するものではない。

---

## 対象 preview

- step: STEP156-B
- preview name: Phase 1 MVP DB schema runtime guard preview
- exporter: `scripts/export_phase1_mvp_db_schema_runtime_guard_preview.py`
- preview JSON: `docs/phase1_mvp_db_schema_runtime_guard_preview.json`
- checker: `scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py`
- readiness registration: STEP156-D
- documentation step: STEP156-E

---

## Preview metadata

runtime guard preview の主要 metadata は以下である。

```text
step=STEP156-B
preview_type=phase1-mvp-db-schema-runtime-guard-preview
connection_mode=runtime-guard-preview-only
safe_mode=True
runtime_guard_preview_only=True
migration_execution_mode=not-executed
ddl_execution_mode=not-executed
```

この preview は runtime guard 条件の記録専用である。  
migration execution mode および DDL execution mode はどちらも `not-executed` である。

---

## Safety flags

runtime guard preview では、以下の実行・書き込みフラグがすべて False でなければならない。

```text
executes_ddl=False
writes_database=False
writes_schema_sql=False
creates_tables=False
alters_tables=False
drops_tables=False
runs_migration=False
modifies_prediction_json=False
writes_prediction_json=False
prediction_core_connected=False
config_enabled=False
history_features_enabled=False
```

この状態により、STEP156-B 〜 STEP156-E は DB・schema・prediction・config に対して変更を加えない。

---

## STEP156-B summary

STEP156-B では runtime guard preview exporter を作成した。

作成ファイル:

- `scripts/export_phase1_mvp_db_schema_runtime_guard_preview.py`
- `docs/phase1_mvp_db_schema_runtime_guard_preview.json`

STEP156-B の期待出力:

```text
Phase 1 MVP DB schema runtime guard preview export: OK
STEP 156-B CHECK: OK
preview_type=phase1-mvp-db-schema-runtime-guard-preview
connection_mode=runtime-guard-preview-only
runtime_guard_preview_only=True
migration_execution_mode=not-executed
ddl_execution_mode=not-executed
executes_ddl=False
writes_database=False
writes_schema_sql=False
creates_tables=False
alters_tables=False
drops_tables=False
runs_migration=False
modifies_prediction_json=False
writes_prediction_json=False
prediction_core_connected=False
config_enabled=False
history_features_enabled=False
minimal_table_count=8
explicit_execute_flag_required=True
default_mode_must_remain_dry_run=True
sqlite_backup_required=True
ddl_candidates_audit_required=True
ddl_candidates_table_count=8
ddl_candidates_danger_pattern_count=0
```

STEP156-B は preview JSON を作成するのみであり、migration・DDL・DB write は行わない。

---

## STEP156-C summary

STEP156-C では runtime guard preview checker を作成した。

作成ファイル:

- `scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py`

STEP156-C の期待出力:

```text
Phase 1 MVP DB schema runtime guard preview validation: OK
STEP 156-C CHECK: OK
preview_type=phase1-mvp-db-schema-runtime-guard-preview
connection_mode=runtime-guard-preview-only
runtime_guard_preview_only=True
migration_execution_mode=not-executed
ddl_execution_mode=not-executed
executes_ddl=False
writes_database=False
writes_schema_sql=False
creates_tables=False
alters_tables=False
drops_tables=False
runs_migration=False
modifies_prediction_json=False
writes_prediction_json=False
prediction_core_connected=False
config_enabled=False
history_features_enabled=False
minimal_table_count=8
explicit_execute_flag_required=True
default_mode_must_remain_dry_run=True
sqlite_backup_required=True
ddl_candidates_audit_required=True
draft_mode=dry-run
ddl_candidates_table_count=8
ddl_candidates_danger_pattern_count=0
execution_preview_step=STEP155-B
race_id_policy=race_id = canonical_race_key
canonical_candidate_key_policy=canonical_candidate_key = race_id + "_" + lane
no_automatic_betting=True
collection_interval_policy=5 to 15 minutes
sqlite_commit_policy=nightly SQLite merge
llm_usage_policy=LLM not used for normal prediction
schema_sql_currently_modified=False
database_currently_modified=False
prediction_json_currently_modified=False
config_currently_modified=False
runtime_guard_preview_currently_modified=False
```

checker は runtime guard preview JSON の安全条件、draft alignment、execution preview alignment、禁止 SQL pattern、rollback requirements、key policy、PDF constraints、PRE_NIGHT constraints、protected file diff を検証する。

---

## STEP156-D summary

STEP156-D では runtime guard preview checker を readiness に登録した。

変更対象:

- `scripts/check_dashboard_readiness_outputs_ready.py`
- `scripts/check_history_database_readiness.py`

登録内容:

- `CHECK_SCRIPTS` に `scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py` を追加
- `CHECKS` に `["python", "scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py"]` を追加
- `REQUIRED_FILES` に `docs/phase1_mvp_db_schema_runtime_guard_preview.json` を追加
- 必要に応じて checker script も required file として登録

STEP156-D 完了後、`python scripts/check_history_database_readiness.py` により `STEP 156-C CHECK: OK` が確認できる。

---

## Phase 1 MVP minimal tables

Phase 1 MVP DB schema migration draft / execution preview / runtime guard preview が対象とする minimal tables は以下の 8 個である。

```text
minimal_table_count=8
```

1. `races`
2. `entries`
3. `feature_sets`
4. `prediction_runs`
5. `predictions`
6. `results`
7. `payouts`
8. `stage_metrics`

---

## Draft alignment

runtime guard preview は STEP154-B の migration draft と整合している必要がある。

```text
draft_script=scripts/migrate_phase1_mvp_db_schema.py
draft_mode=dry-run
draft_step=STEP154-B
draft_checker=STEP154-C
ddl_candidates_table_count=8
ddl_candidates_danger_pattern_count=0
```

migration draft は dry-run only であり、DDL execution や DB write は行わない。

---

## Execution preview alignment

runtime guard preview は STEP155-B の migration execution preview と整合している必要がある。

```text
execution_preview_step=STEP155-B
execution_preview_type=phase1-mvp-db-schema-migration-execution-preview
execution_preview_only=True
migration_execution_mode=not-executed
ddl_execution_mode=not-executed
```

STEP155-B execution preview も migration を実行しない。  
runtime guard preview は、その将来実行条件をさらに明確化するための preview である。

---

## Runtime guard requirements

将来、Phase 1 MVP DB schema migration を実行可能にする場合でも、以下の runtime guard requirements を満たす必要がある。

```text
explicit_execute_flag_required=True
default_mode_must_remain_dry_run=True
clean_git_status_required=True
protected_file_hash_record_required=True
sqlite_backup_required=True
readiness_checks_required=True
ddl_candidates_audit_required=True
create_table_if_not_exists_only=True
destructive_sql_forbidden=True
preserve_history_tables=True
prediction_json_write_forbidden=True
config_enablement_forbidden=True
prediction_core_connection_forbidden=True
automatic_betting_forbidden=True
execution_must_be_separate_explicit_step=True
```

要点:

- 実行には明示的な execution flag が必要である。
- default mode は常に dry-run でなければならない。
- git status は clean でなければならない。
- protected file の hash を事前に記録する。
- `db/boatrace.sqlite3` の backup を必須とする。
- readiness checks を事前実行する。
- DDL_CANDIDATES audit を必須とする。
- 許可される DDL は add-only / idempotent な `CREATE TABLE IF NOT EXISTS` のみ。
- destructive SQL は禁止。
- history tables を保持する。
- `docs/prediction.json` の書き込みは禁止。
- `data/history_feature_config.json` の enablement は禁止。
- prediction core connection は禁止。
- automatic betting は禁止。
- 実 migration は別 STEP として明示的に扱う必要がある。

---

## Allowed future DDL direction

将来候補として許容される方向性は以下のみである。

```text
CREATE TABLE IF NOT EXISTS
```

条件:

- dry-run を default とする
- add-only
- idempotent
- minimal tables のみ
- SQLite backup 後に限る
- clean git status 後に限る
- protected file hash 記録後に限る
- readiness checks OK 後に限る
- DDL_CANDIDATES audit OK 後に限る

---

## Forbidden SQL patterns

runtime guard preview では以下の SQL pattern を禁止する。

```text
DROP TABLE
DROP INDEX
ALTER TABLE
INSERT INTO
UPDATE 
DELETE FROM
REPLACE INTO
TRUNCATE
```

注意:

- `UPDATE ` は trailing space 付きで検出する。
- `updated_at` のような column name による false positive を避けるため、SQL command としての `UPDATE ` を禁止 pattern とする。
- destructive SQL や data mutation SQL は runtime guard 上すべて禁止である。

---

## Rollback requirements

将来 execution を検討する場合、最低限以下の rollback requirements を満たす必要がある。

```text
sqlite_backup_required=True
restore_sqlite_backup=True
git_restore_tracked_files=True
record_git_status_before_execution=True
record_commit_hash_before_execution=True
record_schema_sql_hash_before_execution=True
record_boatrace_sqlite_hash_before_execution=True
record_prediction_json_hash_before_execution=True
record_history_feature_config_hash_before_execution=True
record_sqlite_table_list_before_execution=True
record_sqlite_row_counts_before_execution=True
readiness_checks_before_execution=True
do_not_drop_history_races=True
do_not_drop_history_results=True
```

Rollback 方針:

1. 実行前に `git status` を記録する。
2. 実行前に commit hash を記録する。
3. 実行前に protected files の SHA-256 を記録する。
4. 実行前に `db/boatrace.sqlite3` を backup する。
5. 実行前に SQLite table list と row counts を記録する。
6. 実行前に readiness checks を通す。
7. 問題発生時は SQLite backup を復元する。
8. tracked files は `git restore` で戻す。
9. `history_races` と `history_results` は drop しない。
10. history table を破壊する rollback は行わない。

---

## Protected file hash policy

runtime guard preview では、将来 execution 前に以下の protected files の SHA-256 を記録する必要がある。

```text
db/schema.sql
db/boatrace.sqlite3
docs/prediction.json
data/history_feature_config.json
```

目的:

- migration 前後の差分確認
- rollback 判断
- accidental write の検出
- prediction/config の安全性確認

---

## Protected files unchanged in STEP156-E

STEP156-E では以下を変更しない。

```text
scripts/export_phase1_mvp_db_schema_runtime_guard_preview.py
scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py
docs/phase1_mvp_db_schema_runtime_guard_preview.json
scripts/check_dashboard_readiness_outputs_ready.py
scripts/check_history_database_readiness.py
scripts/migrate_phase1_mvp_db_schema.py
scripts/export_phase1_mvp_db_schema_migration_execution_preview.py
scripts/check_phase1_mvp_db_schema_migration_execution_preview.py
docs/phase1_mvp_db_schema_migration_execution_preview.json
docs/phase1_mvp_db_schema_migration_script_preview.json
docs/phase1_mvp_db_schema_ddl_preview.json
docs/phase1_mvp_db_schema_implementation_plan_preview.json
docs/phase1_mvp_db_schema_preview.json
db/schema.sql
db/boatrace.sqlite3
docs/prediction.json
data/history_feature_config.json
```

STEP156-E で変更可能なのは以下のみである。

```text
README.md
docs/phase1-mvp-db-schema-runtime-guard-preview.md
```

---

## Key policy

Phase 1 MVP DB schema では以下の key policy を採用する。

```text
race_id = canonical_race_key
canonical_race_key = race_date + "_" + venue_id + "_" + race_no
canonical_candidate_key = race_id + "_" + lane
```

この方針により、race 単位および lane/candidate 単位の識別子を安定化する。

---

## PDF operation constraints

PDF 由来の運用制約として以下を保持する。

```text
no_automatic_betting=True
collection_interval_policy=5 to 15 minutes
sqlite_commit_policy=nightly SQLite merge
llm_usage_policy=LLM not used for normal prediction
```

要点:

- automatic betting は行わない。
- collection interval は 5 to 15 minutes。
- SQLite への commit/merge は nightly SQLite merge 方針。
- LLM not used for normal prediction。
- LLM は通常予測の本体には使用しない。

---

## PRE_NIGHT constraints

PRE_NIGHT では、予測時点で利用できない情報を input にしてはならない。

禁止される input 例:

- same-day odds
- final odds
- same-day exhibition information
- same-day weather after prediction cut-off
- confirmed race outcomes
- results
- payouts

方針:

```text
pre_night_only=True
results_and_payouts_allowed_as_pre_night_inputs=False
```

---

## Safety decisions

runtime guard preview における safety decisions は以下である。

```text
migration_execution_mode=not-executed
ddl_execution_mode=not-executed
executes_ddl=False
writes_database=False
writes_schema_sql=False
creates_tables=False
alters_tables=False
drops_tables=False
runs_migration=False
modifies_prediction_json=False
writes_prediction_json=False
prediction_core_connected=False
config_enabled=False
history_features_enabled=False
minimal_table_count=8
```

この状態により、STEP156-B 〜 STEP156-E は preview / validation / documentation の範囲に留まる。

---

## Readiness expected status

STEP156-D 登録後、readiness では以下が確認される。

```text
Phase 1 MVP DB schema runtime guard preview validation: OK
STEP 156-C CHECK: OK
History database readiness validation: OK
```

エラーとして以下が出てはならない。

```text
ERROR:
FAILED
Traceback
PermissionError
TypeError
uncommitted diff
docs/prediction.json has uncommitted diff
```

---

## Current safety status

現在の期待状態は以下である。

```text
runtime_guard_preview_only=True
migration_execution_mode=not-executed
ddl_execution_mode=not-executed
executes_ddl=False
writes_database=False
writes_schema_sql=False
creates_tables=False
alters_tables=False
drops_tables=False
runs_migration=False
modifies_prediction_json=False
writes_prediction_json=False
prediction_core_connected=False
config_enabled=False
history_features_enabled=False
minimal_table_count=8
explicit_execute_flag_required=True
default_mode_must_remain_dry_run=True
sqlite_backup_required=True
ddl_candidates_audit_required=True
draft_mode=dry-run
ddl_candidates_table_count=8
ddl_candidates_danger_pattern_count=0
execution_preview_step=STEP155-B
race_id_policy=race_id = canonical_race_key
canonical_candidate_key_policy=canonical_candidate_key = race_id + "_" + lane
no_automatic_betting=True
collection_interval_policy=5 to 15 minutes
sqlite_commit_policy=nightly SQLite merge
llm_usage_policy=LLM not used for normal prediction
schema_sql_currently_modified=False
database_currently_modified=False
prediction_json_currently_modified=False
config_currently_modified=False
runtime_guard_preview_currently_modified=False
```

---

## Completion criteria for STEP156-E

STEP156-E の完了条件は以下である。

- `docs/phase1-mvp-db-schema-runtime-guard-preview.md` が存在する。
- README に本 Markdown への link が存在する。
- runtime guard preview が documentation-only として記録されている。
- `runtime_guard_preview_only=True` が記録されている。
- `migration_execution_mode=not-executed` が記録されている。
- `ddl_execution_mode=not-executed` が記録されている。
- すべての実行・書き込み flags が False として記録されている。
- `minimal_table_count=8` と 8 tables が記録されている。
- runtime guard requirements が記録されている。
- forbidden SQL patterns が記録されている。
- rollback requirements が記録されている。
- protected file hash policy が記録されている。
- key policy が記録されている。
- PDF operation constraints が記録されている。
- PRE_NIGHT constraints が記録されている。
- 禁止ファイルに差分が無い。
- safety checks が OK。
- 変更ファイルは `README.md` と本 Markdown のみ。
- commit/push が完了している。
- GitHub Actions に赤エラーが無い。
- 最終 `git status` が clean。

---

## Next step

次は STEP156-F として stable tag を作成する。

STEP156-F ではファイル変更を行わない。  
runtime guard preview の documentation 完了状態に対して stable tag を付与する。

