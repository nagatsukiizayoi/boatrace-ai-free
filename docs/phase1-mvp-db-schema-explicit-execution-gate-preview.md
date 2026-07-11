# Phase 1 MVP DB schema explicit execution gate preview 記録

## 概要

この文書は STEP157-B 〜 STEP157-D で作成・検証・readiness 登録した Phase 1 MVP DB schema explicit execution gate preview の状態を記録する。

STEP157-E は documentation-only であり、以下は一切行わない。

- migration 実行
- DDL 実行
- CREATE TABLE 実行
- ALTER TABLE 実行
- DROP TABLE 実行
- INSERT / UPDATE / DELETE / REPLACE / TRUNCATE 実行
- DB write
- db/schema.sql 変更
- db/boatrace.sqlite3 変更
- docs/prediction.json 変更
- data/history_feature_config.json 変更
- preview JSON 変更
- checker / exporter / readiness script 変更
- history feature enablement
- prediction core connection
- automatic betting

この文書は explicit execution gate preview の安全条件、fail closed policy、将来 execution に必要な gate 条件を記録するためのものであり、実際の DB migration を許可または実行するものではない。

## 対象 preview

- step: STEP157-B
- preview name: Phase 1 MVP DB schema explicit execution gate preview
- exporter: scripts/export_phase1_mvp_db_schema_explicit_execution_gate_preview.py
- preview JSON: docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json
- checker: scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py
- readiness registration: STEP157-D
- documentation step: STEP157-E

## Preview metadata

    step=STEP157-B
    preview_type=phase1-mvp-db-schema-explicit-execution-gate-preview
    connection_mode=explicit-execution-gate-preview-only
    safe_mode=True
    explicit_execution_gate_preview_only=True
    migration_execution_mode=not-executed
    ddl_execution_mode=not-executed

この preview は explicit execution gate 条件の記録専用であり、migration execution mode および DDL execution mode はどちらも not-executed である。

## Safety flags

以下の実行・書き込み flags はすべて False である。

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

この状態により、STEP157-B 〜 STEP157-E は preview / validation / documentation の範囲に留まり、DB・schema・prediction・config に対して変更を加えない。

## STEP157-B summary

STEP157-B では explicit execution gate preview exporter を作成した。

作成ファイル:

- scripts/export_phase1_mvp_db_schema_explicit_execution_gate_preview.py
- docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json

期待出力:

    Phase 1 MVP DB schema explicit execution gate preview export: OK
    STEP 157-B CHECK: OK
    preview_type=phase1-mvp-db-schema-explicit-execution-gate-preview
    connection_mode=explicit-execution-gate-preview-only
    explicit_execution_gate_preview_only=True
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
    fail_closed_on_missing_gate=True
    runtime_guard_preview_required=True
    ddl_candidates_table_count=8
    ddl_candidates_danger_pattern_count=0

STEP157-B は preview JSON を作成するのみであり、migration・DDL・DB write は行わない。

## STEP157-C summary

STEP157-C では explicit execution gate preview checker を作成した。

作成ファイル:

- scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py

期待出力:

    Phase 1 MVP DB schema explicit execution gate preview validation: OK
    STEP 157-C CHECK: OK
    preview_type=phase1-mvp-db-schema-explicit-execution-gate-preview
    connection_mode=explicit-execution-gate-preview-only
    explicit_execution_gate_preview_only=True
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
    fail_closed_on_missing_gate=True
    runtime_guard_preview_required=True
    ddl_candidates_table_count=8
    ddl_candidates_danger_pattern_count=0
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
    explicit_execution_gate_preview_currently_modified=False

checker は explicit execution gate preview JSON の安全条件、fail closed policy、rollback requirements、DDL_CANDIDATES audit、key policy、PDF constraints、PRE_NIGHT constraints、protected file diff を検証する。

## STEP157-D summary

STEP157-D では explicit execution gate preview checker を readiness に登録した。

変更対象:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録内容:

- CHECK_SCRIPTS に scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py を追加
- CHECKS に ["python", "scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py"] を追加
- REQUIRED_FILES に scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py を追加
- REQUIRED_FILES に docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json を追加

STEP157-D 完了後、python scripts/check_history_database_readiness.py により STEP 157-C CHECK: OK が確認できる。

## Phase 1 MVP minimal tables

Phase 1 MVP DB schema migration draft / execution preview / runtime guard preview / explicit execution gate preview が対象とする minimal tables は以下の 8 個である。

    minimal_table_count=8

1. races
2. entries
3. feature_sets
4. prediction_runs
5. predictions
6. results
7. payouts
8. stage_metrics

## Explicit execution gate requirements

将来、Phase 1 MVP DB schema migration を実行可能にする場合でも、以下の explicit execution gate requirements をすべて満たす必要がある。

    explicit_execute_flag_required=True
    default_mode_must_remain_dry_run=True
    clean_git_status_required=True
    protected_file_hash_record_required=True
    sqlite_backup_required=True
    readiness_checks_required=True
    ddl_candidates_audit_required=True
    runtime_guard_preview_required=True
    execution_preview_required=True
    migration_draft_required=True
    create_table_if_not_exists_only=True
    destructive_sql_forbidden=True
    preserve_history_tables=True
    prediction_json_write_forbidden=True
    config_enablement_forbidden=True
    prediction_core_connection_forbidden=True
    automatic_betting_forbidden=True
    execution_must_be_separate_explicit_step=True
    fail_closed_on_missing_gate=True

要点:

- 実行には明示的な execution flag が必要である。
- default mode は常に dry-run でなければならない。
- git status は clean でなければならない。
- protected file の hash を事前に記録する。
- db/boatrace.sqlite3 の backup を必須とする。
- readiness checks を事前実行する。
- DDL_CANDIDATES audit を必須とする。
- runtime guard preview が存在し検証済みでなければならない。
- execution preview が存在し検証済みでなければならない。
- migration draft が存在し dry-run として検証済みでなければならない。
- 許可される DDL は add-only / idempotent な CREATE TABLE IF NOT EXISTS のみ。
- destructive SQL は禁止。
- history tables を保持する。
- docs/prediction.json の書き込みは禁止。
- data/history_feature_config.json の enablement は禁止。
- prediction core connection は禁止。
- no automatic betting / automatic betting は禁止。
- 実 migration は別 STEP として明示的に扱う必要がある。
- gate 条件が欠けている場合は fail closed する。

## Fail closed policy

explicit execution gate preview では、以下の fail closed policy を必須とする。

    fail_closed_on_missing_gate=True
    fail_closed_on_dirty_git_status=True
    fail_closed_on_missing_backup=True
    fail_closed_on_missing_hash_record=True
    fail_closed_on_readiness_failure=True
    fail_closed_on_ddl_candidate_audit_failure=True
    fail_closed_on_destructive_sql=True
    fail_closed_on_missing_explicit_execute_flag=True
    fail_closed_on_non_dry_run_default=True

Fail closed 方針:

- gate 条件が 1 つでも未達なら migration を実行しない。
- git status が clean でない場合は migration を実行しない。
- SQLite backup が無い場合は migration を実行しない。
- protected file hash 記録が無い場合は migration を実行しない。
- readiness checks が失敗した場合は migration を実行しない。
- DDL_CANDIDATES audit が失敗した場合は migration を実行しない。
- destructive SQL が検出された場合は migration を実行しない。
- 明示的な execution flag が無い場合は migration を実行しない。
- default mode が dry-run でない場合は migration を実行しない。
- エラーを明示し、rollback 可能な状態を維持する。

## Rollback requirements

将来 execution を検討する場合、最低限以下の rollback requirements を満たす必要がある。

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

Rollback 方針:

1. 実行前に git status を記録する。
2. 実行前に commit hash を記録する。
3. 実行前に protected files の SHA-256 を記録する。
4. 実行前に db/boatrace.sqlite3 を backup する。
5. 実行前に SQLite table list と row counts を記録する。
6. 実行前に readiness checks を通す。
7. 問題発生時は SQLite backup を復元する。
8. tracked files は git restore で戻す。
9. history_races と history_results は drop しない。
10. history table を破壊する rollback は行わない。

## DDL_CANDIDATES audit

explicit execution gate preview は DDL_CANDIDATES audit と整合している必要がある。

    ddl_candidates_table_count=8
    ddl_candidates_danger_pattern_count=0

各 table の DDL は以下を満たす必要がある。

    CREATE TABLE IF NOT EXISTS

許可される方向性:

- dry-run default
- add-only
- idempotent
- minimal tables のみ
- SQLite backup 後に限る
- clean git status 後に限る
- protected file hash 記録後に限る
- readiness checks OK 後に限る
- DDL_CANDIDATES audit OK 後に限る

## Forbidden SQL patterns

explicit execution gate preview では以下の SQL pattern を禁止する。

    DROP TABLE
    DROP INDEX
    ALTER TABLE
    INSERT INTO
    UPDATE 
    DELETE FROM
    REPLACE INTO
    TRUNCATE

注意:

- UPDATE は trailing space 付きの UPDATE  として検出する。
- updated_at のような column name による false positive を避けるため、SQL command としての UPDATE  を禁止 pattern とする。
- destructive SQL や data mutation SQL は explicit execution gate 上すべて禁止である。

## References to prior steps

explicit execution gate preview は、以下の prior previews / draft と整合する必要がある。

    runtime_guard_preview_json=docs/phase1_mvp_db_schema_runtime_guard_preview.json
    runtime_guard_preview_step=STEP156-B
    runtime_guard_checker=STEP156-C
    execution_preview_json=docs/phase1_mvp_db_schema_migration_execution_preview.json
    execution_preview_step=STEP155-B
    migration_draft_script=scripts/migrate_phase1_mvp_db_schema.py
    migration_draft_step=STEP154-B
    migration_draft_checker=STEP154-C

関連 STEP:

- STEP154-B: migration draft 作成。dry-run only。
- STEP154-C: migration draft checker 作成。
- STEP155-B: migration execution preview 作成。not-executed。
- STEP155-C: migration execution preview checker 作成。
- STEP156-B: runtime guard preview 作成。
- STEP156-C: runtime guard preview checker 作成。
- STEP157-B: explicit execution gate preview 作成。
- STEP157-C: explicit execution gate preview checker 作成。
- STEP157-D: readiness 登録。

## Protected file hash policy

explicit execution gate preview では、将来 execution 前に以下の protected files の SHA-256 を記録する必要がある。

    db/schema.sql
    db/boatrace.sqlite3
    docs/prediction.json
    data/history_feature_config.json
    docs/phase1_mvp_db_schema_runtime_guard_preview.json
    docs/phase1_mvp_db_schema_migration_execution_preview.json

目的:

- migration 前後の差分確認
- rollback 判断
- accidental write の検出
- prediction/config の安全性確認
- runtime guard / execution preview との整合確認

## Protected files unchanged in STEP157-E

STEP157-E では以下を変更しない。

    scripts/export_phase1_mvp_db_schema_explicit_execution_gate_preview.py
    scripts/check_phase1_mvp_db_schema_explicit_execution_gate_preview.py
    docs/phase1_mvp_db_schema_explicit_execution_gate_preview.json
    scripts/check_dashboard_readiness_outputs_ready.py
    scripts/check_history_database_readiness.py
    scripts/migrate_phase1_mvp_db_schema.py
    scripts/export_phase1_mvp_db_schema_runtime_guard_preview.py
    scripts/check_phase1_mvp_db_schema_runtime_guard_preview.py
    docs/phase1_mvp_db_schema_runtime_guard_preview.json
    docs/phase1_mvp_db_schema_migration_execution_preview.json
    docs/phase1_mvp_db_schema_migration_script_preview.json
    docs/phase1_mvp_db_schema_ddl_preview.json
    docs/phase1_mvp_db_schema_implementation_plan_preview.json
    docs/phase1_mvp_db_schema_preview.json
    db/schema.sql
    db/boatrace.sqlite3
    docs/prediction.json
    data/history_feature_config.json
    requirements.txt

STEP157-E で変更可能なのは以下のみである。

    README.md
    docs/phase1-mvp-db-schema-explicit-execution-gate-preview.md

## Key policy

Phase 1 MVP DB schema では以下の key policy を採用する。

    race_id = canonical_race_key
    canonical_race_key = race_date + "_" + venue_id + "_" + race_no
    canonical_candidate_key = race_id + "_" + lane

この方針により、race 単位および lane/candidate 単位の識別子を安定化する。

## PDF operation constraints

PDF 由来の運用制約として以下を保持する。

    no_automatic_betting=True
    collection_interval_policy=5 to 15 minutes
    sqlite_commit_policy=nightly SQLite merge
    llm_usage_policy=LLM not used for normal prediction

要点:

- no automatic betting / automatic betting は行わない。
- collection interval は 5 to 15 minutes。
- SQLite への commit/merge は nightly SQLite merge 方針。
- LLM not used for normal prediction。
- LLM は通常予測の本体には使用しない。

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

    pre_night_only=True
    results_and_payouts_allowed_as_pre_night_inputs=False
    same_day_odds_allowed=False
    final_odds_allowed=False
    confirmed_outcomes_allowed=False

## Safety decisions

explicit execution gate preview における safety decisions は以下である。

    explicit_execution_gate_preview_only=True
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
    fail_closed_on_missing_gate=True
    runtime_guard_preview_required=True
    ddl_candidates_table_count=8
    ddl_candidates_danger_pattern_count=0

この状態により、STEP157-B 〜 STEP157-E は preview / validation / documentation の範囲に留まる。

## Readiness expected status

STEP157-D 登録後、readiness では以下が確認される。

    Phase 1 MVP DB schema explicit execution gate preview validation: OK
    STEP 157-C CHECK: OK
    History database readiness validation: OK

エラーとして以下が出てはならない。

    ERROR:
    FAILED
    Traceback
    PermissionError
    TypeError
    uncommitted diff
    docs/prediction.json has uncommitted diff

docs/prediction.json が readiness 実行後に変更された場合は commit せず、必ず restore する。

## Current safety status

現在の期待状態は以下である。

    explicit_execution_gate_preview_only=True
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
    fail_closed_on_missing_gate=True
    runtime_guard_preview_required=True
    ddl_candidates_table_count=8
    ddl_candidates_danger_pattern_count=0
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
    explicit_execution_gate_preview_currently_modified=False

## Completion criteria for STEP157-E

STEP157-E の完了条件は以下である。

- docs/phase1-mvp-db-schema-explicit-execution-gate-preview.md が存在する。
- README に本 Markdown への link が存在する。
- explicit execution gate preview が documentation-only として記録されている。
- explicit_execution_gate_preview_only=True が記録されている。
- migration_execution_mode=not-executed が記録されている。
- ddl_execution_mode=not-executed が記録されている。
- すべての実行・書き込み flags が False として記録されている。
- minimal_table_count=8 と 8 tables が記録されている。
- explicit execution gate requirements が記録されている。
- fail closed policy が記録されている。
- rollback requirements が記録されている。
- DDL_CANDIDATES audit が記録されている。
- forbidden SQL patterns が記録されている。
- references to STEP156/155/154 が記録されている。
- key policy が記録されている。
- PDF operation constraints が記録されている。
- PRE_NIGHT constraints が記録されている。
- 禁止ファイルに差分が無い。
- safety checks が OK。
- 変更ファイルは README.md と本 Markdown のみ。
- commit/push が完了している。
- GitHub Actions に赤エラーが無い。
- 最終 git status が clean。

## Next step

次は STEP157-F として stable tag を作成する。

STEP157-F ではファイル変更を行わない。  
explicit execution gate preview の documentation 完了状態に対して stable tag を付与する。

