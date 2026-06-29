# 履歴特徴量 candidate key schema decision 記録

## 概要

この文書は、STEP149-A および STEP149-B で確認・決定した candidate key schema 方針を記録するものです。

STEP149-A では、STEP148-A の key normalization preview をもとに、candidate key の正規化によって一致数が改善したかを監査しました。

STEP149-B では、その結果を踏まえて、今後の shadow-only matching および Phase 1 MVP DB schema preview に向けた canonical key 方針を決定しました。

この文書は設計判断の記録であり、実装ではありません。

## 現在の安全方針

以下の安全方針を維持します。

- data/history_feature_config.json は enabled:false のまま維持する
- prediction core へ直接接続しない
- connection_mode=shadow-only を維持する
- docs/prediction.json を変更しない
- preview JSON を変更しない
- 予測スコアを変更しない
- 順位を変更しない
- 推奨買い目を変更しない
- 期待値を変更しない
- DB schema を変更しない
- dashboard 表示を追加しない

## STEP149-A key normalization effectiveness audit

STEP149-A では、以下のファイルを確認しました。

- docs/prediction_history_feature_key_normalization_preview.json
- scripts/check_history_feature_key_normalization_preview.py
- scripts/check_history_database_readiness.py
- docs/prediction.json

主な確認項目は以下です。

- prediction_key_count
- shadow_key_count
- matched_after_normalization_count
- matched_normalized_keys_sample
- normalization_samples

STEP149-A の目的は、STEP148-A の key normalization preview によって candidate key matching が改善する可能性があるかを確認することでした。

## STEP149-A decision rule

STEP149-A では、以下の判定ルールを採用しました。

- matched_after_normalization_count > 0 の場合:
  - key normalization は有効である可能性がある
  - 次に shadow-only matching に正規化ルールを安全に組み込む設計を検討する
- matched_after_normalization_count == 0 または missing の場合:
  - 単純な文字列正規化では不十分である
  - candidate key schema の違いを調査・整理する

いずれの場合も、prediction core への接続は行いません。

## STEP149-B candidate key schema decision

STEP149-B では、今後の candidate key schema として以下の方針を決定しました。

## canonical_race_key

canonical_race_key は以下の要素から構成します。

- race_date
- venue_id
- race_no

推奨する概念形式:

- canonical_race_key = race_date + venue_id + race_no

推奨する文字列表現:

- canonical_race_key = race_date + "_" + venue_id + "_" + race_no

## canonical_candidate_key

canonical_candidate_key は以下の要素から構成します。

- race_date
- venue_id
- race_no
- lane

推奨する概念形式:

- canonical_candidate_key = race_date + venue_id + race_no + lane

推奨する文字列表現:

- canonical_candidate_key = race_date + "_" + venue_id + "_" + race_no + "_" + lane

## 各要素の意味

### race_date

race_date はレース開催日を表します。

推奨形式:

- YYYYMMDD

理由:

- 同一 venue_id、同一 race_no のレースは日付ごとに存在するため
- prediction_runs、feature_sets、results との紐付けに必要なため

### venue_id

venue_id は競艇場を識別する安定したコードまたは正規化済み識別子です。

理由:

- 同一日に複数場で同じ race_no が存在するため
- venue_name は表記揺れが起こり得るため
- Phase 1 MVP DB schema で races、entries、results を安定して接続するため

### race_no

race_no はレース番号です。

推奨範囲:

- 1 から 12

理由:

- 同じ日、同じ場に複数レースが存在するため
- races、entries、predictions、results の基本的な紐付けに必要なため

### lane

lane は枠番または艇番として扱う 1 から 6 の整数です。

理由:

- 1レース内の各 candidate を識別するため
- entries の primary key は将来的に race_id + lane になるため
- results も race_id + lane で接続する想定であるため

## primary key 要素にしないもの

以下は canonical_candidate_key の primary key 要素にしません。

- racer_name
- motor_no
- boat_no
- odds
- popularity
- exhibition_time
- exhibition_st
- exhibition_course
- weather
- wind_speed
- wave_height
- result
- payout

## primary key 要素にしない理由

### racer_name

racer_name は表記揺れ、漢字、空白、旧字体などの差異が起こる可能性があります。

そのため、candidate identity の主キー要素にはしません。

### motor_no / boat_no

motor_no および boat_no は特徴量としては重要ですが、candidate identity の主キー要素にはしません。

理由:

- モーター・ボートは race candidate の属性であり、identity そのものではないため
- 将来的には feature として扱うべき情報であるため

### odds / popularity

odds および popularity は当日更新情報です。

PRE_NIGHT では利用禁止情報です。

そのため、candidate key の主キー要素には絶対に含めません。

### exhibition_time / exhibition_st / exhibition_course

展示情報は POST_EXHIBITION 以降で使用可能な情報です。

PRE_NIGHT candidate identity には含めません。

### weather / wind_speed / wave_height

天候・水面情報は MORNING 以降で使用可能な情報です。

candidate identity ではなく、stage-specific feature として扱います。

### result / payout

結果および払戻は未来情報・評価情報です。

予測 candidate の key には絶対に含めません。

## race_id との関係

将来的に DB schema を作成する際、races.race_id は canonical_race_key と同じ意味を持つべきです。

推奨方針:

- races.race_id = canonical_race_key

ただし、既存データに race_id が存在する場合は、その構成要素を確認してから採用します。

確認対象:

- race_date が含まれているか
- venue_id が含まれているか
- race_no が含まれているか
- 表記が安定しているか
- 同じレースを一意に識別できるか

## entries との関係

Phase 1 MVP DB schema では、entries は以下を基本にします。

- PRIMARY KEY (race_id, lane)

ここで race_id は canonical_race_key と同義にする方針です。

これにより、1レース内の6艇を安定して識別できます。

## predictions との関係

predictions では、candidate を識別するために以下を使う方針です。

- race_id
- lane
- stage
- bet_type
- combination

1着確率、2連対確率、3連対確率などの艇単位予測では、race_id + lane が基本になります。

3連単などの組み合わせ予測では、combination を別途持ちます。

## results との関係

results は以下を基本にします。

- PRIMARY KEY (race_id, lane)

これにより、予測時の candidate と結果を安全に照合できます。

## feature_sets との関係

feature_sets は race_id と stage を持つ方針です。

candidate 単位の特徴量はファイル側または別構造で管理し、feature_set_id と hash で追跡します。

## prediction_runs との関係

prediction_runs は race_id、stage、model_version、feature_version、code_version を記録します。

candidate key schema が安定していることで、prediction_runs と predictions を安全に接続できます。

## 添付設計書との関係

添付の競艇AI予想システム最終設計では、Phase 1 として事前予想MVPを構築する方針です。

Phase 1 では以下が予定されています。

- 番組表取得
- SQLite 保存
- PRE_NIGHT 特徴量生成
- PRE_NIGHT モデル作成
- 前日夜予想出力
- GitHub Pages 表示
- 結果取得
- PRE_NIGHT 評価

これらを実装する前に、candidate key schema を明確にする必要があります。

理由:

- races と entries の紐付けが必要
- prediction_runs と predictions の紐付けが必要
- predictions と results の照合が必要
- stage_metrics の評価対象を安定させる必要
- PRE_NIGHT で未来情報を混入させないため

## STEP150 系との関係

STEP149-C の後は、STEP150 系で Phase 1 MVP DB schema preview に進む予定です。

想定される次工程:

- STEP150-A: Phase 1 MVP DB schema audit
- STEP150-B: minimal DB schema preview
- STEP150-C: DB schema checker
- STEP150-D: DB schema documentation

STEP150 系では、今回決定した canonical_race_key と canonical_candidate_key を前提として、最小 DB schema を検討します。

## 現時点でまだ実装しないこと

現時点では、以下はまだ実装しません。

- canonical key 生成処理
- prediction core への接続
- docs/prediction.json の変更
- DB schema の変更
- races テーブル作成
- entries テーブル作成
- predictions テーブル作成
- results テーブル作成
- PRE_NIGHT 予想本体
- モデル推論
- 期待値計算
- 買い目推奨

## 確認済みチェック

以下のチェックが OK であることを確認対象とします。

- STEP 122 CHECK: OK
- STEP 148-B CHECK: OK
- STEP 146-B CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## 変更していないもの

STEP149-A、STEP149-B、STEP149-C では以下を変更しません。

- data/history_feature_config.json
- docs/prediction.json
- docs/prediction_history_feature_key_normalization_preview.json
- docs/prediction_history_feature_core_shadow_connection_preview.json
- docs/prediction_history_feature_shadow_preview.json
- docs/index.html
- scripts/*.py
- db/schema.sql
- db/boatrace.sqlite3
- data/import/*
- data/raw/*

## 禁止事項

明示的に許可されるまで、以下は禁止です。

- enabled:true にする
- prediction core に直接接続する
- docs/prediction.json を変更する
- preview JSON を本番 prediction output として扱う
- 予測スコアを変更する
- 順位を変更する
- 推奨買い目を変更する
- 期待値を変更する
- DB schema を変更する
- dashboard 表示に反映する
- 自動投票を実装する

## 結論

STEP149-B で、今後の candidate key schema 方針を以下のように決定しました。

- canonical_race_key = race_date + venue_id + race_no
- canonical_candidate_key = race_date + venue_id + race_no + lane

この方針により、Phase 1 MVP DB schema preview へ進む準備が整います。

ただし、現時点ではまだ実装せず、shadow-only と enabled:false を維持します。
