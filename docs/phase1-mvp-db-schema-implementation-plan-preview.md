# Phase 1 MVP DB schema implementation plan preview 記録

## 概要

この文書は、STEP151-A から STEP151-D までで実施した Phase 1 MVP DB schema implementation plan preview の内容を記録するものです。

本ステップは、Phase 1 MVP DB schema の実装計画を確認・検証するための planning-only preview です。

この段階では、実際の DB schema 変更、SQLite DB 変更、テーブル作成、migration 実行、prediction core 接続、予測出力変更は行いません。

## 対象 preview

- step: STEP151-B
- preview_type: phase1-mvp-db-schema-implementation-plan
- connection_mode: planning-only
- safe_mode: true

## STEP151-A: implementation plan audit

STEP151-A では、Phase 1 MVP DB schema の実装計画を audit しました。

確認した主な内容は以下です。

- Phase 1 MVP に必要な minimal tables
- canonical key policy
- implementation_order
- 既存 history tables の保全方針
- rollback_policy
- PRE_NIGHT safety constraints
- db/schema.sql の現状確認
- db/boatrace.sqlite3 の現状確認
- docs/prediction.json が変更されていないこと
- repository が clean であること

STEP151-A は audit-only であり、DB schema や DB file は変更していません。

## STEP151-B: implementation plan preview export

STEP151-B では、implementation plan preview exporter を作成し、以下の preview JSON を出力しました。

- exporter: scripts/export_phase1_mvp_db_schema_implementation_plan_preview.py
- preview JSON: docs/phase1_mvp_db_schema_implementation_plan_preview.json

この preview JSON は、Phase 1 MVP DB schema 実装前の計画を design / planning レベルで記録するものです。

出力された preview は以下の安全設定を持ちます。

- connection_mode: planning-only
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- runs_migration:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false

## STEP151-C: checker 作成

STEP151-C では、preview JSON の内容を検証する checker を作成しました。

- checker: scripts/check_phase1_mvp_db_schema_implementation_plan_preview.py

checker は以下を確認します。

- preview JSON が存在すること
- step が STEP151-B であること
- preview_type が phase1-mvp-db-schema-implementation-plan であること
- connection_mode が planning-only であること
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- runs_migration:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false
- minimal_table_count=8
- implementation_order が正しいこと
- rollback_policy が存在すること
- PRE_NIGHT safety constraints が記録されていること
- db/schema.sql に未コミット差分がないこと
- db/boatrace.sqlite3 に未コミット差分がないこと
- docs/prediction.json に未コミット差分がないこと

確認済みの代表的な出力は以下です。

- Phase 1 MVP DB schema implementation plan preview validation: OK
- STEP 151-C CHECK: OK

## STEP151-D: readiness 登録

STEP151-D では、STEP151-C の checker を readiness checks に登録しました。

変更対象は以下の 2 ファイルのみです。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録された checker は以下です。

- scripts/check_phase1_mvp_db_schema_implementation_plan_preview.py

登録された required JSON は以下です。

- docs/phase1_mvp_db_schema_implementation_plan_preview.json

readiness 実行時には、以下の OK が確認されます。

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

## Implementation order

Phase 1 MVP DB schema の推奨 implementation_order は以下です。

text: races -> entries -> feature_sets -> prediction_runs -> predictions -> results -> payouts -> stage_metrics

この順序は、race 単位の基礎情報から entry、feature、prediction、result、payout、stage metrics へ段階的に依存関係を積み上げるためのものです。

## Canonical key policy

STEP149 で決定した canonical key policy を継続します。

### canonical_race_key

text: canonical_race_key = race_date + "_" + venue_id + "_" + race_no

構成要素:

- race_date
- venue_id
- race_no

### canonical_candidate_key

text: canonical_candidate_key = race_date + "_" + venue_id + "_" + race_no + "_" + lane

構成要素:

- race_date
- venue_id
- race_no
- lane

## Primary key に含めない項目

以下は primary key / canonical key には含めません。

- racer_name
- motor_no
- boat_no
- odds
- exhibition_time
- weather
- result
- payout

理由:

- 表記揺れが発生しやすい
- future information になり得る
- PRE_NIGHT 時点では使用できない情報が含まれる
- 結果・払戻は予測時点で未知のため key に含めない

## PRE_NIGHT safety constraints

PRE_NIGHT 予測では、予測時点で取得できない情報を使用しません。

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

使用可能な情報は、PRE_NIGHT 時点で既知の race / entry / historical data に限定します。

## Rollback policy

rollback_policy は以下の方針とします。

### 1. 変更前 hash の記録

schema 実装に進む前に、以下の hash または状態を記録します。

- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json

### 2. git restore による復元

schema.sql や docs/prediction.json に意図しない差分が出た場合は、git restore で戻します。

対象:

- db/schema.sql
- docs/prediction.json
- data/history_feature_config.json

### 3. SQLite DB の保全

db/boatrace.sqlite3 は慎重に扱います。

Phase 1 の実装前には backup を作成し、migration を行う場合は rollback 可能な状態にします。

### 4. 既存 history tables の保全

既存の history tables は preserve します。

- history_races
- history_results

これらは削除・再作成・破壊的変更を行いません。

## Existing history tables policy

既存 history tables は preserved とします。

- existing_history_tables_preserved:true
- history_races preserved
- history_results preserved

Phase 1 MVP DB schema の新規設計は、既存履歴データを破壊しない形で進めます。

## Safety flags

この preview / planning 段階では、以下を維持します。

- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- runs_migration:false
- modifies_prediction_json:false
- writes_prediction_json:false
- prediction_core_connected:false
- config_enabled:false
- history_features_enabled:false

## 変更していないファイル

以下のファイルは変更していません。

- db/schema.sql
- db/boatrace.sqlite3
- docs/prediction.json
- data/history_feature_config.json
- docs/phase1_mvp_db_schema_implementation_plan_preview.json

## 禁止事項

STEP151-E では以下を行いません。

- db/schema.sql の変更
- db/boatrace.sqlite3 の変更
- table creation
- migration execution
- prediction core connection
- data/history_feature_config.json の enabled:true 変更
- docs/prediction.json の変更
- prediction score の変更
- prediction rank の変更
- recommendation の変更
- expected value の変更
- dashboard UI 追加
- preview JSON の変更

## Readiness check status

STEP151-D までに readiness 登録済みです。

確認対象:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

期待される OK line:

- STEP 151-C CHECK: OK
- STEP 150-C CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## 現在の状態

現時点では、Phase 1 MVP DB schema implementation plan は planning-only preview として確定しています。

- DB schema は未変更
- DB file は未変更
- prediction output は未変更
- prediction core は未接続
- history feature config は disabled
- migration は未実行
- table creation は未実行

## 次ステップ

STEP151-E 完了後は、stable tag を作成する STEP151-F に進みます。

STEP151-F では file modification は行わず、現在の safe planning state に tag を付与します。
