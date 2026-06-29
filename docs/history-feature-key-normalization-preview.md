# 履歴特徴量 key normalization preview 記録

## 概要

この文書は、STEP148-A、STEP148-B、STEP148-C で実施した履歴特徴量 key normalization preview の記録です。

本 preview の目的は、STEP147-A の candidate key matching audit で確認された matched_candidate_count=0 について、prediction candidate と shadow candidate の key 表記差異を安全に調査することです。

この段階では、履歴特徴量を prediction core に接続しません。
また、docs/prediction.json、予測スコア、順位、推奨買い目、期待値は変更しません。

## 現在の安全方針

以下の方針を維持します。

- data/history_feature_config.json は enabled:false のまま維持する
- connection_mode=shadow-only を維持する
- core_connection_enabled:false を維持する
- affects_prediction_output:false を維持する
- writes_prediction_json:false を維持する
- history_features_enabled:false を維持する
- prediction_core_connected:false を維持する
- prediction core へ直接接続しない
- docs/prediction.json を変更しない
- 予測スコアを変更しない
- 順位を変更しない
- 推奨買い目を変更しない
- 期待値を変更しない

## STEP148-A exporter

STEP148-A では、key normalization preview exporter を作成しました。

作成ファイル:

- scripts/export_history_feature_key_normalization_preview.py
- docs/prediction_history_feature_key_normalization_preview.json

目的:

- prediction candidate key と shadow candidate key の表記差異を確認する
- 正規化後に candidate key が一致する可能性を preview する
- matched_after_normalization_count を確認する
- prediction core には接続しない
- docs/prediction.json は変更しない

期待された出力:

- History feature key normalization preview export: OK
- STEP 148-A CHECK: OK
- connection_mode=shadow-only
- core_connection_enabled=False
- affects_prediction_output=False
- writes_prediction_json=False
- history_features_enabled=False

## STEP148-A preview JSON

STEP148-A で生成した preview JSON は以下です。

- docs/prediction_history_feature_key_normalization_preview.json

この JSON には以下の内容が含まれます。

- step=STEP148-A
- preview_type=candidate-key-normalization
- connection_mode=shadow-only
- config_enabled:false
- core_connection_enabled:false
- affects_prediction_output:false
- writes_prediction_json:false
- history_features_enabled:false
- prediction_core_connected:false
- original_core_shadow_preview_counts
- normalization_rules
- normalization_preview_counts
- prediction_key_count
- shadow_key_count
- matched_after_normalization_count
- matched_normalized_keys_sample
- normalization_samples
- decision

## STEP148-B checker

STEP148-B では、key normalization preview の検証用 checker を作成しました。

作成ファイル:

- scripts/check_history_feature_key_normalization_preview.py

この checker は、以下を検証します。

- preview JSON が存在すること
- step が STEP148-A であること
- preview_type が candidate-key-normalization であること
- connection_mode が shadow-only であること
- config_enabled が False であること
- core_connection_enabled が False であること
- affects_prediction_output が False であること
- writes_prediction_json が False であること
- history_features_enabled が False であること
- prediction_core_connected が False であること
- docs/prediction.json に未コミット差分がないこと
- data/history_feature_config.json が enabled:false であること

期待された出力:

- History feature key normalization preview validation: OK
- STEP 148-B CHECK: OK

## STEP148-B での補足修正

STEP148-B の実行時に、original_core_shadow_preview_counts 内の optional 項目が None になるケースを確認しました。

例:

- prediction_candidate_count=None

これは core shadow preview JSON 側で optional 項目が存在しない、または null になる場合があるためです。

そのため checker 側では、optional な count 項目について None を許容するようにしました。

この修正は、予測結果や prediction core への接続には影響しません。

## STEP148-C readiness integration

STEP148-C では、key normalization preview checker を既存の readiness check に登録しました。

変更ファイル:

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/check_history_database_readiness.py

登録した checker:

- scripts/check_history_feature_key_normalization_preview.py

登録した required file:

- docs/prediction_history_feature_key_normalization_preview.json

目的:

- dashboard readiness で key normalization preview の存在と安全性を確認する
- history database readiness で key normalization preview の存在と安全性を確認する
- GitHub Actions 上でも STEP 148-B CHECK: OK を確認できるようにする

## STEP148-C での補足修正

readiness 登録後、scripts/check_history_feature_key_normalization_preview.py が直接実行され、Permission denied になる問題を確認しました。

原因:

- readiness の CHECKS に script path だけを登録していたため、Python 経由ではなく直接実行されていた

修正方針:

- CHECKS では以下の形式にする

- python scripts/check_history_feature_key_normalization_preview.py

この修正により、readiness 実行時に checker が Python 経由で実行されるようになりました。

## 確認済みチェック

以下のチェックが OK であることを確認しました。

- STEP 122 CHECK: OK
- STEP 146-B CHECK: OK
- STEP 148-B CHECK: OK
- STEP 112 CHECK: OK
- Dashboard readiness outputs validation: OK
- History database readiness validation: OK

## matched_candidate_count=0 の扱い

STEP147-A および STEP146 系で、core shadow connection preview では以下が確認されています。

- candidate_count=11
- matched_candidate_count=0
- missing_candidate_count=11

この matched_candidate_count=0 は、shadow-only preview 段階ではエラー扱いしません。

理由:

- prediction core へ接続していない
- prediction output に影響していない
- docs/prediction.json を変更していない
- key の形式差異を調査する段階である
- 正規化 preview によって、今後の key matching 改善方針を決めるため

## matched_after_normalization_count の確認方針

STEP148-A の key normalization preview では、以下を確認対象とします。

- prediction_key_count
- shadow_key_count
- matched_after_normalization_count
- matched_normalized_keys_sample
- normalization_samples

今後の STEP149-A では、matched_after_normalization_count を確認し、正規化によって candidate key matching が改善するかを監査します。

## 今後の判断方針

### matched_after_normalization_count が増えている場合

key normalization は有効である可能性があります。

次に検討すること:

- 正規化ルールを shadow-only adapter に安全に組み込む方法
- まだ prediction core には接続しない
- docs/prediction.json は変更しない
- enabled:false を維持する

### matched_after_normalization_count が 0 のままの場合

単純な文字列正規化では不十分な可能性があります。

次に調査すること:

- prediction 側 candidate key の構成
- shadow 側 candidate key の構成
- race_id の形式
- venue_id の形式
- race_no の形式
- lane または boat_no の形式
- 日付形式
- candidate key schema の違い

## 添付設計書との関係

添付の競艇AI予想システム最終設計では、最終的に以下の Phase へ進む予定です。

- Phase 1: 事前予想MVP
- Phase 2: 当日朝更新
- Phase 3: 展示後更新
- Phase 4: オッズ・期待値判定
- Phase 5: 継続改善

現在の STEP148 は、Phase 1 に入る前の安全準備工程です。

特に、履歴特徴量と prediction candidate の対応関係を安全に確認するための preview 段階です。

## DB 構築方針との関係

現時点では、本格的な DB スキーマ構築にはまだ進みません。

理由:

- candidate key matching がまだ確定していない
- matched_candidate_count=0 の原因確認が必要
- race_id、venue_id、race_no、lane などの key schema 方針を先に固める必要がある
- 本格 DB スキーマを先に作ると、後から key 設計を修正する可能性が高い

したがって、DB 構築は以下の順序で進めます。

- STEP149-A: key normalization effectiveness audit
- STEP149-B: candidate key schema decision
- STEP149-C: candidate key schema documentation
- STEP150-A: Phase 1 MVP DB schema audit
- STEP150-B: minimal DB schema preview
- STEP150-C: DB schema checker
- STEP150-D: DB schema documentation

## 現時点で構築済みの DB

現時点では、履歴特徴量 preview および readiness 用に以下を使用しています。

- db/boatrace.sqlite3
- history_results
- history_races

この DB は、history database readiness のために必要です。

ただし、STEP148-D では DB ファイル自体は変更しません。

## 変更していないもの

STEP148-A、STEP148-B、STEP148-C を通じて、以下は変更していません。

- data/history_feature_config.json
- docs/prediction.json
- docs/index.html
- prediction core
- 予測スコア
- 順位
- 推奨買い目
- 期待値
- DB スキーマ
- 本格 prediction pipeline

## 禁止事項

今後の STEP149 以降でも、明示的に許可されるまで以下は禁止です。

- enabled:true にする
- prediction core に直接接続する
- docs/prediction.json を変更する
- preview JSON を本番 prediction output として扱う
- 予測スコアを変更する
- 順位を変更する
- 推奨買い目を変更する
- 期待値を変更する
- DB スキーマを変更する
- dashboard 表示に反映する

## 次のステップ

次は STEP148-E で stable tag を作成します。

推奨タグ名:

- history-feature-key-normalization-preview-stable

その後、STEP149-A で key normalization effectiveness audit を実施します。

STEP149-A の目的:

- matched_after_normalization_count を確認する
- 正規化によって candidate key matching が改善したかを判断する
- candidate key schema の次方針を決める
- まだ prediction core には接続しない
- enabled:false を維持する
- docs/prediction.json は変更しない

## 結論

STEP148-A、STEP148-B、STEP148-C により、key normalization preview の exporter、checker、readiness integration が完了しました。

この preview は shadow-only であり、prediction core には接続していません。

data/history_feature_config.json は enabled:false のままです。

docs/prediction.json は変更していません。

今後は STEP149-A で、matched_after_normalization_count を中心に、key normalization の有効性を監査します。
