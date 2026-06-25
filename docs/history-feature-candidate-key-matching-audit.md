# 履歴特徴量 candidate key matching audit 記録

## 概要

このドキュメントは、STEP147-A candidate key matching audit の結果を記録するものです。

STEP146-A から STEP146-E では、履歴特徴量の core shadow connection preview を作成し、checker と readiness 統合、ドキュメント化、stable tag 作成まで完了しました。

STEP147-A では、その preview で matched_candidate_count=0 となっている理由を調査するため、prediction 側候補キーと shadow 側候補キーの構造を確認しました。

本ステップでは実装変更は行っていません。

## 現在の安全方針

現在の安全方針は以下です。

- data/history_feature_config.json は enabled:false を維持する
- prediction core へ直接接続しない
- docs/prediction.json を変更しない
- preview JSON を prediction output に反映しない
- 予測スコアを変更しない
- 予測順位を変更しない
- 推奨買い目を変更しない
- 期待値を変更しない
- connection mode は shadow-only を維持する

STEP147-A は調査のみであり、prediction output には影響しません。

## STEP147-A の目的

STEP147-A の目的は以下です。

- core shadow connection preview の candidate count を確認する
- matched_candidate_count=0 の原因を調査する
- prediction 側の candidate key 構造を確認する
- shadow 側の candidate key 構造を確認する
- missing candidates の診断情報を確認する
- 次の isolated key-normalization preview に向けた方針を整理する

## STEP146 の状態

STEP146 時点の core shadow connection preview は以下の状態でした。

- connection_mode=shadow-only
- core_connection_enabled=False
- affects_prediction_output=False
- history_features_enabled=False
- candidate_count=11
- matched_candidate_count=0
- missing_candidate_count=11

matched_candidate_count=0 は、現時点では失敗ではありません。

理由は以下です。

- まだ本接続ではない
- prediction core へ直接接続していない
- shadow-only の isolated preview である
- candidate matching の診断段階である
- prediction output に影響しない

## STEP147-A で作成したログ

STEP147-A では、以下のログを /tmp/history_feature_147a/ に作成しました。

- config_enabled_check.txt
- prediction_json_sha256_before.txt
- prediction_json_sha256_after.txt
- core_shadow_preview_structure.txt
- prediction_candidate_key_dump.txt
- shadow_candidate_key_dump.txt
- missing_candidates_inspection.txt
- candidate_key_matching_plan.txt
- check_history_feature_config.log
- check_core_shadow_connection_preview.log
- history_database_readiness.log
- git_status_final.txt
- step147a_summary.txt

これらのログは repository にはコミットしません。

## config 確認

STEP147-A では、data/history_feature_config.json の enabled が false であることを確認しました。

期待された結果:

- enabled=False
- CONFIG_ENABLED_FALSE_OK

このため、履歴特徴量はまだ有効化されていません。

## prediction.json の確認

STEP147-A では、docs/prediction.json の hash を before / after で保存し、差分がないことを確認しました。

確認内容:

- docs/prediction.json hash before を保存
- docs/prediction.json hash after を保存
- before と after が一致
- git diff docs/prediction.json が空
- prediction output は未変更

docs/prediction.json は STEP147-A では変更していません。

## core shadow preview 構造確認

STEP147-A では、docs/prediction_history_feature_core_shadow_connection_preview.json の構造を確認しました。

重要項目:

- step=STEP146-A
- connection_mode=shadow-only
- core_connection_enabled=False
- affects_prediction_output=False
- history_features_enabled=False
- candidate_count=11
- matched_candidate_count=0
- missing_candidate_count=11

この結果から、preview は安全な shadow-only 状態を維持していることを確認しました。

## prediction 側候補キー確認

STEP147-A では、docs/prediction.json 側の candidate / race / rank / score 系のキー構造を確認しました。

目的:

- prediction 側の候補データがどの構造で存在しているか確認する
- race date, venue, race number, boat number などの候補キーを探す
- 今後の key normalization preview に必要な情報を集める

この確認は読み取りのみであり、docs/prediction.json は変更していません。

## shadow 側候補キー確認

STEP147-A では、以下の shadow preview 系 JSON の candidate / match / missing 系キーを確認しました。

- docs/prediction_history_feature_shadow_preview.json
- docs/prediction_history_feature_core_shadow_connection_preview.json

目的:

- shadow 側に存在する候補キー構造を確認する
- prediction 側と照合できそうなキーを調査する
- missing candidates の原因を調査する

この確認も読み取りのみです。

## missing candidates 診断

STEP147-A では、core shadow connection preview 内の missing candidate 情報を確認しました。

目的:

- matched_candidate_count=0 の理由を確認する
- prediction 側候補と shadow 側候補の key mismatch を把握する
- 次の isolated key-normalization preview で使う候補キーを整理する

現時点では matched_candidate_count=0 は許容されます。

## history database readiness の一時失敗と復旧

STEP147-A の途中で history database readiness が一時的に失敗しました。

エラー内容:

- missing table: history_results
- missing table: history_races

原因:

- ローカルの db/boatrace.sqlite3 が未構築、または history table が不足していた

対応:

- scripts/build_history_database.py を実行
- history database build が成功
- STEP 108 CHECK: OK を確認
- history_results と history_races の作成を確認
- history database readiness を再実行
- History database readiness validation: OK を確認
- STEP 112 CHECK: OK を確認

この問題は prediction core や shadow preview の問題ではなく、ローカル DB の未構築によるものです。

## 確認済み OK 行

STEP147-A で確認した重要な OK 行は以下です。

- CONFIG_ENABLED_FALSE_OK
- STEP 122 CHECK: OK
- STEP 146-B CHECK: OK
- STEP 108 CHECK: OK
- STEP 112 CHECK: OK
- History database readiness validation: OK

## candidate key matching plan

STEP147-A では、次の段階に向けて candidate key matching plan を作成しました。

高レベルの候補キー:

- race date
- venue
- race number
- boat number
- racer id
- racer name
- prediction candidate index as fallback

ただし、prediction candidate index は最終手段として扱います。

## 使用しないもの

candidate key matching では、以下は使用しません。

- score mutation
- rank mutation
- recommendation mutation
- expected value mutation
- direct prediction core connection
- enabled:true

## 次の方針

次の方針は isolated key-normalization preview です。

これは、prediction core に接続せず、docs/prediction.json を変更せず、shadow-only のまま candidate key normalization を試すための preview です。

次段階で行うべきこと:

- isolated key-normalization preview exporter を作成する
- prediction 側候補キーと shadow 側候補キーを正規化して比較する
- matched_candidate_count の改善可能性を診断する
- ただし prediction output には反映しない
- enabled:false を維持する
- prediction core 未接続を維持する

## 禁止事項

今後の作業でも、以下は禁止です。

- enabled:true にすること
- prediction core へ直接接続すること
- docs/prediction.json を変更すること
- preview JSON を prediction output に反映すること
- 予測スコアを変更すること
- 予測順位を変更すること
- 推奨買い目を変更すること
- 期待値を変更すること
- DB schema を変更すること
- data/import や data/raw を不要に変更すること

## git 状態

STEP147-A は /tmp/history_feature_147a/ にログを作るだけの調査 step です。

repository に変更を残さないことを確認しました。

最終条件:

- git status clean
- docs/prediction.json 差分なし
- data/history_feature_config.json enabled:false
- prediction core 未接続
- 予測出力未変更

## 結論

STEP147-A により、matched_candidate_count=0 の状態は shadow-only preview では許容されることを確認しました。

また、次の作業は prediction core に接続することではなく、isolated key-normalization preview を作成して、候補キーの安全な正規化と照合可能性を診断することです。

現時点では、enabled:false を維持し、docs/prediction.json を変更せず、prediction core 未接続のまま進めます。
