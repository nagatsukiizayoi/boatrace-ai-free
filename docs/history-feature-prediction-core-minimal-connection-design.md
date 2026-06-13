# 履歴特徴量 prediction core 最小安全接続案

## 概要

このドキュメントは、STEP140-A / STEP140-B の調査結果をもとに、履歴特徴量を prediction core へ接続する場合の最小安全接続案を記録する。

現時点では、履歴特徴量は prediction core に接続していない。

本ドキュメントは設計のみであり、実装変更は行わない。

## 現在の安全状態

data/history_feature_config.json は現在も disabled のままである。

    {
      "enabled": false
    }

以下は実施しない。

- enabled:true への変更
- docs/prediction.json の変更
- 予測スコア計算への履歴特徴量反映
- 予測順位への履歴特徴量反映
- 推奨買い目への履歴特徴量反映
- 期待値計算への履歴特徴量反映
- prediction core の実装変更

## 背景

STEP137-D 以降で、履歴特徴量 adapter dry-run と adapter preview を整備した。

STEP138-A / STEP138-B では adapter preview を dashboard に表示し、readiness に統合した。

STEP139-A / STEP139-B では final diff audit を実施し、docs/prediction.json の一時的な hash 変化が既存 dashboard compatibility 補正に由来することを確認した。

STEP140-A / STEP140-B では、prediction core 接続候補を調査し、writer / generator / adapter usage / racer_id / config guard の参照箇所を確認した。

## 最小安全接続の基本方針

履歴特徴量を prediction core に接続する場合でも、最初の段階では score や rank を変更しない。

最初の接続は、以下のような shadow / diagnostic 接続に限定する。

- prediction candidate に racer_id を使って履歴特徴量を添付する
- 添付結果を history_feature_context または history_feature_shadow として持つ
- enabled:false の間は score / rank / recommendation / expected_value に反映しない
- output への追加も preview JSON に限定する
- docs/prediction.json は変更しない

## 接続候補レイヤー

STEP140-A の調査から、接続候補は大きく以下に分類する。

1. prediction output generator
2. dashboard compatibility patcher
3. dashboard validator
4. readiness checker
5. adapter preview exporter
6. actual score / recommendation calculation logic

最小安全接続では、まず actual score / recommendation calculation logic には触れない。

最初に扱うべき候補は、adapter preview exporter または prediction output generator の直後の shadow 層である。

## 接続してはいけない初期対象

初期段階では、以下に直接接続しない。

- score calculation
- rank calculation
- recommendation ordering
- expected_value calculation
- odds calculation
- production docs/prediction.json writer
- dashboard compatibility patcher の既存補正ロジック

理由は、影響範囲が大きく、既存 prediction output の安定性を損なう可能性があるためである。

## racer_id 接続方針

履歴特徴量は racer_id をキーとして取得する。

ただし prediction 側では以下のようなキーが存在し得る。

- racer_id
- racerId
- player_id
- playerId
- registration_number
- toban
- 登番

adapter 側では、これらを normalize して racer_id として扱う。

ID が存在しない場合は、履歴特徴量を missing とし、default values を返す。

## default values 方針

ID が無い、または履歴特徴量が見つからない場合は、以下のような default values を返す。

- race_count: 0
- win_rate: 0.0
- top2_rate: 0.0
- top3_rate: 0.0
- avg_start_timing: 0.0
- history_feature_available: false
- history_feature_source: default_values

default values は、enabled:false の間は score に影響させない。

## shadow field 案

最初の接続では、以下のような shadow field を preview にだけ追加する。

    history_feature_shadow:
      enabled: false
      available: true
      source: racer_history_features.csv
      affects_prediction_output: false
      prediction_output_modified: false
      features:
        race_count: 120
        win_rate: 0.18
        top2_rate: 0.34
        top3_rate: 0.52
        avg_start_timing: 0.16

この情報は diagnostics 用であり、prediction score には使わない。

## config guard

接続コードを設計する場合、必ず data/history_feature_config.json の top-level enabled を確認する。

enabled:false の場合:

- history features may be loaded
- preview / diagnostics may be generated
- score must not change
- rank must not change
- recommendation must not change
- expected_value must not change
- docs/prediction.json must not be overwritten

enabled:true の場合の処理は、別ステップで設計・監査する。

## docs/prediction.json の扱い

STEP139-A/B により、scripts/ensure_prediction_json_dashboard_compat.py が docs/prediction.json を dashboard compatibility のために補正する既存仕様があることを確認した。

そのため、prediction core 接続時は以下を守る。

- docs/prediction.json を直接 shadow 接続の出力先にしない
- まず preview JSON に限定する
- docs/prediction.json に変更が発生した場合は必ず diff を確認する
- 意図しない変更は git restore docs/prediction.json で戻す
- dashboard compatibility patcher と history feature connection を混同しない

## 段階的接続計画

### Phase 1: shadow preview

- adapter を使って履歴特徴量を取得する
- preview JSON に history_feature_shadow を追加する
- score / rank / recommendation / expected_value は変更しない
- readiness と dashboard で確認する

### Phase 2: A/B shadow comparison

- base prediction と shadow preview を比較する
- missing_candidate_count を確認する
- default values の割合を確認する
- racer_id normalization の成功率を確認する

### Phase 3: controlled score experiment

- enabled:false のまま別ファイルでスコア変化を試算する
- docs/prediction.json は変更しない
- recommendation ordering は変更しない
- 影響量を report に記録する

### Phase 4: pre-enable review

- enabled:true 化前に final audit を行う
- rollback tag を作成する
- GitHub Actions を確認する
- prediction core 変更範囲を最小化する

## 初回実装時の禁止事項

初回実装では以下を禁止する。

- enabled:true にする
- score に履歴特徴量を加算する
- rank を変える
- recommendation を並べ替える
- expected_value を変える
- docs/prediction.json を更新する
- dashboard compatibility patcher に履歴特徴量ロジックを混ぜる
- config guard なしで履歴特徴量を参照する

## 初回実装候補

初回実装候補は、production prediction core ではなく、shadow preview exporter とする。

候補:

- scripts/export_history_feature_adapter_preview.py の拡張
- または新規 scripts/export_history_feature_shadow_preview.py の作成

推奨は新規ファイルである。

理由:

- 既存 preview を壊さない
- docs/prediction.json を触らない
- rollback しやすい
- readiness に段階的に追加できる
- dashboard 表示も分離できる

## 初回実装の出力候補

新規 preview JSON の候補は以下である。

- docs/prediction_history_feature_shadow_preview.json

このファイルには、base prediction の情報と履歴特徴量 shadow 情報を含める。

ただし、prediction score / rank / recommendation / expected_value は変更しない。

## 検証方針

初回実装後には以下を確認する。

- JSON syntax check
- history_features_enabled が false
- affects_prediction_output が false
- prediction_output_modified が false
- prediction_json_modified が false
- candidate_count が妥当
- matched_candidate_count が妥当
- missing_candidate_count が妥当
- docs/prediction.json hash が変わらない
- git status が clean または想定ファイルのみ

## rollback 方針

問題が発生した場合は、以下の stable tag に戻す。

- history-feature-final-diff-audit-stable
- history-feature-adapter-preview-dashboard-stable
- history-feature-adapter-dry-run-stable
- history-feature-pre-enable-audit-stable
- history-feature-ab-preview-stable

## 結論

STEP140-C では、prediction core への直接接続ではなく、shadow preview を初回実装候補とする。

この方針により、履歴特徴量を prediction pipeline 近くで確認しつつ、score / rank / recommendation / expected_value / docs/prediction.json を変更しない安全な検証が可能になる。

次のステップでは、この設計に基づいて shadow preview exporter を実装する。
