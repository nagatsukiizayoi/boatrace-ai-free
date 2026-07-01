# Phase 1 MVP DB schema preview 記録

## 概要

この文書は、STEP150-A、STEP150-B、STEP150-C、STEP150-D で実施した Phase 1 MVP DB schema preview の記録です。

添付の競艇AI予想システム最終設計では、最初の実装段階として Phase 1: 事前予想MVP が定義されています。

Phase 1 の目的は、前日夜時点で利用可能な情報だけを使い、PRE_NIGHT 予想を安全に生成・保存・評価することです。

本 STEP150 系では、そのために必要となる最小 DB schema を、実装前に preview として整理しました。

この段階では、DB schema は変更していません。
また、db/boatrace.sqlite3、db/schema.sql、docs/prediction.json は変更していません。

## 現在の安全方針

STEP150 系では以下を維持します。

- data/history_feature_config.json は enabled:false のまま維持する
- prediction core へ直接接続しない
- connection_mode=design-only
- history_features_enabled:false
- config_enabled:false
- prediction_core_connected:false
- affects_prediction_output:false
- modifies_prediction_json:false
- writes_prediction_json:false
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- docs/prediction.json を変更しない
- db/schema.sql を変更しない
- db/boatrace.sqlite3 を変更しない
- DB テーブルを作成しない
- 予測スコアを変更しない
- 順位を変更しない
- 推奨買い目を変更しない
- 期待値を変更しない

## STEP150-A Phase 1 MVP DB schema audit

STEP150-A では、Phase 1 MVP に必要な最小 DB schema の audit を実施しました。

確認した内容:

- 既存 DB の状態
- db/schema.sql の存在
- 既存 data、docs、scripts の構成
- Phase 1 MVP に必要な最小テーブル案
- PRE_NIGHT で使ってはいけない情報
- canonical key 方針との整合

既存 DB の確認対象:

- db/boatrace.sqlite3
- history_results
- history_races

確認済み:

- history_results_exists=True
- history_races_exists=True

## STEP150-A で確認した key 方針

STEP149-B/C で確定した key 方針を STEP150 系でも継続します。

- canonical_race_key = race_date + venue_id + race_no
- canonical_candidate_key = race_date + venue_id + race_no + lane

この key 方針は、Phase 1 MVP の以下の接続に必要です。

- races と entries
- races と prediction_runs
- prediction_runs と predictions
- predictions と results
- results と payouts
- stage_metrics の評価対象

## STEP150-B exporter

STEP150-B では、Phase 1 MVP DB schema preview exporter を作成しました。

作成ファイル:

- scripts/export_phase1_mvp_db_schema_preview.py
- docs/phase1_mvp_db_schema_preview.json

目的:

- Phase 1 MVP に必要な最小 DB schema を JSON として preview 出力する
- db/schema.sql は変更しない
- db/boatrace.sqlite3 は変更しない
- docs/prediction.json は変更しない
- DB テーブルは作成しない

期待された出力:

- Phase 1 MVP DB schema preview export: OK
- STEP 150-B CHECK: OK
- preview_type=phase1-mvp-db-schema
- connection_mode=design-only
- writes_schema_sql=False
- writes_database=False
- creates_tables=False
- modifies_prediction_json=False
- prediction_core_connected=False

## STEP150-B preview JSON

STEP150-B で生成した preview JSON は以下です。

- docs/phase1_mvp_db_schema_preview.json

主な内容:

- step=STEP150-B
- preview_type=phase1-mvp-db-schema
- connection_mode=design-only
- safe_mode=True
- config_enabled:false
- history_features_enabled:false
- prediction_core_connected:false
- affects_prediction_output:false
- modifies_prediction_json:false
- writes_prediction_json:false
- writes_schema_sql:false
- writes_database:false
- creates_tables:false
- alters_tables:false
- minimal_table_count=8
- canonical_race_key
- canonical_candidate_key
- PRE_NIGHT forbidden information
- optional early tables
- deferred tables

## STEP150-C checker

STEP150-C では、Phase 1 MVP DB schema preview JSON を検証する checker を作成しました。

作成ファイル:

- scripts/check_phase1_mvp_db_schema_preview.py

この checker は以下を検証します。

- docs/phase1_mvp_db_schema_preview.json が存在すること
- step=STEP150-B であること
- preview_type=phase1-mvp-db-schema であること
- connection_mode=design-only であること
- config_enabled=False であること
- history_features_enabled=False であること
- prediction_core_connected=False であること
- modifies_prediction_json=False であること
- writes_prediction_json=False であること
- writes_schema_sql=False であること
- writes_database=False であること
- creates_tables=False であること
- alters_tables=False であること
- minimal_table_count=8 であること
- 必須8テーブルが含まれること
- canonical_race_key の components が race_date, venue_id, race_no であること
- canonical_candidate_key の components が race_date, venue_id, race_no, lane であること
- db/schema.sql に差分がないこと
- db/boatrace.sqlite3 に差分がないこと
- docs/prediction.json に差分がないこと

期待された出力:

- Phase 1 MVP DB schema preview validation: OK
- STEP 150-C CHECK: OK

## STEP150-C での補足修正

STEP150-C の checker 実行時に、optional_early_tables の検証が厳しすぎる問題を確認しました。

原因:

- optional_early_tables は概要 preview であり、primary_key や suggested_columns は必須ではない
- しかし checker が minimal_tables と同じ厳格さで検証していた

修正方針:

- minimal_tables は primary_key と suggested_columns を必須とする
- optional_early_tables と deferred_tables は table_name、role、reason、deferred_until などの概要確認に緩和する

この修正は preview checker の妥当化であり、DB schema や prediction output には影響しません。

## STEP150-D readiness integration

STEP150-D では、Phase 1 MVP DB schema preview checker を既存 readiness check に登録しました。

変更ファイル:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録した checker:

- scripts/check_phase1_mvp_db_schema_preview.py

登録した required file:

- docs/phase1_mvp_db_schema_preview.json

登録方針:

- CHECK_SCRIPTS には script path 文字列として登録する
- CHECKS には Python 経由の実行形式で登録する
- REQUIRED_FILES には preview JSON を登録する

正しい形式:

- CHECK_SCRIPTS: scripts/check_phase1_mvp_db_schema_preview.py
- CHECKS: python scripts/check_phase1_mvp_db_schema_preview.py
- REQUIRED_FILES: docs/phase1_mvp_db_schema_preview.json

## STEP150-D での補足修正

readiness 登録時に、CHECK_SCRIPTS に list 形式が入ったことで TypeError が発生しました。

原因:

- CHECK_SCRIPTS は py_compile 用の script path 文字列を想定している
- そこに Python command list を入れると、py_compile の join 処理で TypeError になる

修正方針:

- CHECK_SCRIPTS は文字列にする
- CHECKS は Python command list にする

この修正により、dashboard readiness と history database readiness が正常に通るようになりました。

## minimal_table_count

STEP150-B/C で確認した最小テーブル数は以下です。

- minimal_table_count=8

## Phase 1 MVP minimal tables

Phase 1 MVP の最小 DB schema preview では、以下の8テーブルを対象にしました。

### races

役割:

- 1レースにつき1行を保存する
- race_id は canonical_race_key と整合させる

key 方針:

- race_id = canonical_race_key
- canonical_race_key = race_date + venue_id + race_no

### entries

役割:

- 1レース内の6艇を保存する
- candidate identity は race_id + lane で識別する

key 方針:

- PRIMARY KEY (race_id, lane)
- canonical_candidate_key = race_date + venue_id + race_no + lane

### feature_sets

役割:

- 生成した特徴量ファイルの metadata を保存する
- feature body は DB へ全量保存せず、file path と hash で追跡する方針

主な要素:

- feature_set_id
- race_id
- stage
- as_of_time
- feature_version
- feature_hash
- feature_file_path

### prediction_runs

役割:

- 予測実行単位を保存する
- race_id、stage、model_version、feature_version、code_version を追跡する

目的:

- 再現性の確保
- どの入力・特徴量・モデルで予測したかを後から確認する

### predictions

役割:

- 予測確率や将来の期待値関連項目を保存する

Phase 1 PRE_NIGHT での扱い:

- odds は null でもよい
- expected_value は null でもよい
- is_recommended は false または null でもよい

### results

役割:

- レース結果を race_id + lane 単位で保存する
- PRE_NIGHT 予想の評価に使用する

key 方針:

- PRIMARY KEY (race_id, lane)

### payouts

役割:

- 払戻を race_id + bet_type + combination 単位で保存する
- ROI 評価や将来の期待値検証に使用する

key 方針:

- PRIMARY KEY (race_id, bet_type, combination)

### stage_metrics

役割:

- stage ごとの集計評価指標を保存する

Phase 1 での対象:

- PRE_NIGHT

主な評価指標:

- races_count
- bets_count
- hit_count
- hit_rate
- roi
- logloss
- brier_score

## optional early tables

Phase 1 MVP の後、早期に追加してよい候補は以下です。

- model_registry
- training_runs
- ingestion_runs

### model_registry

役割:

- model_version
- stage
- model_type
- validation metrics
- active model 管理

### training_runs

役割:

- 学習実行履歴
- training period
- validation period
- metrics_json

### ingestion_runs

役割:

- データ取得履歴
- source type
- target date
- status
- error_message
- raw_file_path

## deferred tables

以下は Phase 1 MVP では後回しにします。

- weather_water_snapshots
- exhibition_snapshots
- odds_snapshots
- prediction_changes
- stage_transition_metrics
- racer_stats_snapshot
- motor_boat_stats_snapshot
- venue_bias_daily

## deferred 理由

### weather_water_snapshots

MORNING 以降で必要になります。

PRE_NIGHT では当日天候や水面情報を使わないため、Phase 1 MVP では deferred とします。

### exhibition_snapshots

POST_EXHIBITION 以降で必要になります。

PRE_NIGHT では展示情報を使わないため、Phase 1 MVP では deferred とします。

### odds_snapshots

PRE_EXHIBITION または FINAL 以降で必要になります。

PRE_NIGHT では当日オッズを使わないため、Phase 1 MVP では deferred とします。

### prediction_changes

複数 stage の予測差分を比較する段階で必要になります。

Phase 1 の PRE_NIGHT 単独では deferred とします。

### stage_transition_metrics

PRE_NIGHT から MORNING、POST_EXHIBITION、FINAL への改善を評価する段階で必要になります。

Phase 1 の PRE_NIGHT 単独では deferred とします。

### racer_stats_snapshot

PRE_NIGHT の特徴量ソースとして将来的に重要です。

ただし、最小 MVP schema preview では、先に races、entries、features、prediction、results の流れを固定します。

### motor_boat_stats_snapshot

モーター・ボート特徴量の保存に将来必要です。

ただし、Phase 1 MVP の最初の schema preview では deferred とします。

### venue_bias_daily

場別傾向の保存に将来必要です。

ただし、Phase 1 MVP の最初の schema preview では deferred とします。

## PRE_NIGHT forbidden information

PRE_NIGHT では以下を使用しません。

- same-day odds
- exhibition_time
- exhibition_st
- exhibition_course
- same-day wind_speed
- same-day wave_height
- same-day weather snapshots not available at previous night
- results
- payouts
- final odds
- popularity after market movement

理由:

- 未来情報の混入を防ぐため
- 事前予想モデルの評価を正しく保つため
- PRE_NIGHT と後続 stage の役割を分離するため

## 添付設計書との関係

添付の競艇AI予想システム最終設計では、実装順序として以下が示されています。

- Phase 1: 事前予想MVP
- Phase 2: 当日朝更新
- Phase 3: 展示後更新
- Phase 4: オッズ・期待値判定
- Phase 5: 継続改善

STEP150 系は、Phase 1 に入る前の DB schema preview です。

Phase 1 では以下が予定されています。

- 番組表取得
- SQLite 保存
- PRE_NIGHT 特徴量生成
- PRE_NIGHT モデル作成
- 前日夜予想出力
- GitHub Pages 表示
- 結果取得
- PRE_NIGHT 評価

STEP150 では、そのうち保存・評価に必要な最小 schema を設計 preview として整理しました。

## まだ実装していないこと

STEP150 系では、以下はまだ実装していません。

- db/schema.sql の変更
- db/boatrace.sqlite3 の変更
- DB テーブル作成
- migration 実行
- prediction core 接続
- PRE_NIGHT 予想本体
- 番組表取得
- PRE_NIGHT 特徴量生成
- PRE_NIGHT モデル推論
- GitHub Pages 予想表示
- 結果取得
- PRE_NIGHT 評価実装
- 期待値計算
- 買い目推奨

## 確認済みチェック

以下が OK であることを確認しています。

- STEP 150-C CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 122 CHECK: OK
- STEP 112 CHECK: OK
- Dashboard readiness outputs validation: OK
- History database readiness validation: OK

## 変更していないもの

STEP150-A、STEP150-B、STEP150-C、STEP150-D を通じて、以下は変更していません。

- db/schema.sql
- db/boatrace.sqlite3
- data/history_feature_config.json
- docs/prediction.json
- docs/index.html
- prediction core
- 予測スコア
- 順位
- 推奨買い目
- 期待値
- DB tables

## 禁止事項

明示的に許可されるまで、以下は禁止です。

- db/schema.sql を変更する
- db/boatrace.sqlite3 を変更する
- DB テーブルを作成する
- data/history_feature_config.json を enabled:true にする
- prediction core に直接接続する
- docs/prediction.json を変更する
- preview JSON を本番 prediction output として扱う
- 予測スコアを変更する
- 順位を変更する
- 推奨買い目を変更する
- 期待値を変更する
- dashboard 表示を追加する
- 自動投票を実装する

## 次のステップ

次は STEP150-F で stable tag を作成します。

推奨タグ名:

- phase1-mvp-db-schema-preview-stable

その後は、STEP151 系として Phase 1 MVP DB schema implementation preview または schema migration plan に進みます。

ただし、実際に db/schema.sql や db/boatrace.sqlite3 を変更する前に、必ず schema implementation plan を文書化します。

## 結論

STEP150-A から STEP150-D により、Phase 1 MVP DB schema preview の audit、exporter、checker、readiness integration が完了しました。

この preview は design-only であり、DB schema や database は変更していません。

Phase 1 MVP の最小テーブルは8個です。

- races
- entries
- feature_sets
- prediction_runs
- predictions
- results
- payouts
- stage_metrics

今後は stable tag を作成した後、DB schema implementation plan へ進みます。
