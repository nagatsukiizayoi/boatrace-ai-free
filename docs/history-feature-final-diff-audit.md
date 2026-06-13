# 履歴特徴量 prediction core 接続前 final diff audit

## 概要

このドキュメントは、STEP139-A で実施した prediction core 接続前の final diff audit 結果を記録する。

目的は、履歴特徴量 adapter preview / dashboard / readiness の追加が、予測ロジック本体や docs/prediction.json に意図しない変更を与えていないことを確認することである。

現時点では、履歴特徴量は prediction core に接続していない。

## 現在の安全状態

data/history_feature_config.json は現在も disabled のままである。

    {
      "enabled": false
    }

以下は実施していない。

- enabled:true への変更
- docs/prediction.json の変更コミット
- 予測スコア計算への履歴特徴量反映
- 予測順位への履歴特徴量反映
- 推奨買い目への履歴特徴量反映
- 期待値計算への履歴特徴量反映
- prediction core の変更

## STEP139-A 監査で確認した内容

STEP139-A では、主に以下を確認した。

- git status が clean であること
- data/history_feature_config.json が enabled:false であること
- docs/prediction.json の sha256 hash を監査すること
- history feature 関連参照箇所を検索すること
- prediction.json writer を再確認すること
- prediction logic keywords を再確認すること
- 既存の safety / adapter / dashboard / readiness check を実行すること
- 最終的に git status が clean であること

## 検出した重要な例外事項

STEP139-A では、docs/prediction.json の hash が一時的に変化するケースを検出した。

調査の結果、原因は以下である。

- scripts/check_dashboard_readiness_outputs_ready.py
- scripts/ensure_prediction_json_dashboard_compat.py

check_dashboard_readiness_outputs_ready.py は、内部で ensure_prediction_json_dashboard_compat.py を実行する。

ensure_prediction_json_dashboard_compat.py は、docs/prediction.json を dashboard 表示互換形式へ補正する既存スクリプトである。

このため、この readiness を no-change audit の中でそのまま実行すると、docs/prediction.json の hash が変わる。

## hash 変化の原因

デバッグ結果では、以下を確認した。

    HASH_CHANGED_BY=scripts/ensure_prediction_json_dashboard_compat.py

この変更は、履歴特徴量 adapter preview によるものではない。

## ensure_prediction_json_dashboard_compat.py の役割

ensure_prediction_json_dashboard_compat.py は、docs/prediction.json に dashboard 表示互換用の項目を補完する。

確認された主な補完項目は以下である。

- races
- recommendations
- recommendation_id
- race_id
- race_no
- venue_name
- bet_type
- combination
- selection
- odds
- expected_value
- expectedValue
- ev
- expected_return
- expected_return_rate
- value_grade
- reason_version
- confidence
- score
- amount
- recommendation_reason
- reason
- reason_text
- reason_points
- risk_note
- risk

## 差分の扱い

STEP139-A では、ensure_prediction_json_dashboard_compat.py による差分を確認したあと、docs/prediction.json を restore した。

つまり、検出された docs/prediction.json の変更は commit していない。

監査ログは以下に保存した。

- /tmp/history_feature_139a/ensure_prediction_json_diff_stat.txt
- /tmp/history_feature_139a/ensure_prediction_json_diff_head.txt
- /tmp/history_feature_139a/final_audit_summary.txt

## final audit の結論

STEP139-A の最終状態は以下である。

- docs/prediction.json は restore 済み
- git status は clean
- data/history_feature_config.json は enabled:false
- 履歴特徴量 adapter preview は prediction core に未接続
- prediction core は未変更
- 予測スコア・順位・推奨買い目・期待値は未変更
- hash 変化の原因は既存 dashboard compatibility 補正であり、履歴特徴量ではない

## 今後の注意点

今後、prediction core 接続前の no-change audit を行う場合、以下に注意する。

- scripts/check_dashboard_readiness_outputs_ready.py は docs/prediction.json を補正する場合がある
- no-change audit では、実行後に必ず git diff / git status を確認する
- docs/prediction.json が変更された場合は、内容確認後に git restore docs/prediction.json を行う
- ensure_prediction_json_dashboard_compat.py の補正は dashboard compatibility 目的として扱う
- prediction core 接続前に、補正処理と本番予測出力生成処理の責務を分離することが望ましい

## prediction core 接続前の条件

履歴特徴量を prediction core に接続する前に、以下を確認する。

- enabled:false のまま dry-run / preview / A/B の差分を確認済み
- adapter preview と A/B preview の役割が整理済み
- racer_id 正規化方針が確認済み
- missing_candidate_count の扱いが確認済み
- default values の影響が確認済み
- dashboard compatibility 補正による docs/prediction.json 変更を理解済み
- rollback tag が存在する
- GitHub Actions が赤エラーなし
- prediction core への変更範囲が最小化されている

## 関連 stable tag

現在の安全状態に関連する tag は以下である。

- history-feature-ab-preview-stable
- history-feature-pre-enable-audit-stable
- history-feature-adapter-dry-run-stable
- history-feature-adapter-preview-dashboard-stable

## 結論

STEP139-A により、prediction core 接続前の final diff audit を実施した。

一時的な docs/prediction.json の hash 変化は検出されたが、原因は既存の dashboard compatibility 補正スクリプトであり、履歴特徴量 adapter preview ではない。

docs/prediction.json は restore 済みで、最終状態は clean である。

現時点で履歴特徴量は enabled:false のままであり、prediction core には未接続である。
