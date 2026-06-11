# 履歴特徴量 予測 adapter 設計書

## 概要

このドキュメントは、履歴特徴量を将来的に予測処理へ安全に渡すための adapter 設計を記録する。

STEP137-A / STEP137-B により、予測ロジック接続前の入口調査を実施した。  
その結果を踏まえ、まずは予測本体を変更せず、`enabled:false` のまま履歴特徴量を安全に扱う adapter 層を設計する。

現時点では、履歴特徴量は予測ロジック本体に反映しない。

## 現在の安全状態

現在の設定は以下である。

    {
      "enabled": false
    }

このため、以下を維持する。

- 予測スコアを変更しない
- 予測順位を変更しない
- 推奨買い目を変更しない
- 期待値を変更しない
- `docs/prediction.json` を変更しない
- dashboard の既存表示を壊さない

## adapter の目的

adapter の目的は、既存予測処理と履歴特徴量ローダーの間に安全な中間層を作ることである。

主な役割は以下。

1. 予測 JSON または予測処理内の選手 ID を受け取る
2. ID を `racer_id` に正規化する
3. `scripts/history_feature_loader.py` から履歴特徴量を取得する
4. 欠損時は default values を返す
5. `enabled:false` の場合は予測スコアに影響させない
6. preview / A/B preview / diagnostics 用にのみ履歴特徴量を返す

## 関連ファイル

- `scripts/history_feature_loader.py`
- `scripts/check_history_feature_loader.py`
- `scripts/check_prediction_history_feature_join.py`
- `scripts/export_prediction_history_feature_preview.py`
- `scripts/check_prediction_history_feature_preview.py`
- `scripts/export_history_feature_ab_preview.py`
- `scripts/check_history_feature_ab_preview.py`
- `scripts/check_dashboard_history_feature_ab_preview.py`
- `data/history_feature_config.json`
- `data/import/history/racer_history_features.csv`
- `docs/prediction.json`
- `docs/index.html`

## ID 正規化方針

既存予測側では、選手 ID が以下の名前で現れる可能性がある。

- `racer_id`
- `player_id`
- `racerId`
- `playerId`
- `registration_number`
- `toban`
- `登番`

adapter では、これらを受け取り、履歴特徴量 CSV の `racer_id` と照合できる形へ正規化する。

正規化ルール案。

- `None` は欠損扱い
- 空文字は欠損扱い
- 数値は文字列に変換する
- 前後の空白を除去する
- 日本語キー `登番` も候補として扱う

## 欠損時 default values

履歴特徴量が見つからない場合は、`data/history_feature_config.json` の default values を利用する。

想定される default values の例。

    {
      "race_count": 0,
      "win_rate": 0.0,
      "top2_rate": 0.0,
      "top3_rate": 0.0,
      "avg_start_timing": 0.0
    }

欠損時には、以下のような補助情報を付与する。

    {
      "history_feature_available": false,
      "history_feature_source": "default_values"
    }

## enabled:false 時の動作

`enabled:false` の場合、adapter は履歴特徴量を取得しても、予測スコア計算には渡さない。

許可される用途。

- dry-run preview
- A/B preview
- diagnostics
- dashboard 表示
- readiness check

禁止される用途。

- 予測順位の変更
- 推奨買い目の変更
- 期待値の変更
- 本番予測 JSON の既存構造変更
- `docs/prediction.json` の上書き

## 将来的な adapter 関数案

将来的には、以下のような関数を検討する。

    normalize_racer_id(value) -> str | None
    extract_racer_id(candidate: dict) -> str | None
    attach_history_feature_preview(candidate: dict) -> dict
    build_history_feature_context(prediction: dict) -> dict

ただし、STEP137-C 時点では実装しない。

## 安全な出力フィールド案

将来 preview または diagnostics 用に付与する場合は、既存フィールドを上書きせず、以下のような独立フィールドを使う。

    {
      "history_feature_preview": {
        "enabled": false,
        "available": true,
        "source": "racer_history_features.csv",
        "features": {
          "race_count": 120,
          "win_rate": 0.18
        }
      }
    }

このフィールドは preview 用であり、予測順位・期待値・買い目には影響させない。

## A/B preview との関係

既に以下の A/B preview が存在する。

- `docs/prediction_history_feature_ab_preview.json`
- `scripts/export_history_feature_ab_preview.py`
- `scripts/check_history_feature_ab_preview.py`

adapter は、まず A/B preview 側で使用し、既存予測出力との差分確認に利用するのが安全である。

## readiness check 方針

adapter 実装後は、以下を確認するチェックを追加する。

- config が存在すること
- `enabled:false` が維持されていること
- ID 正規化が想定通りであること
- 欠損 ID で default values が返ること
- 既存 prediction JSON が変更されないこと
- 統合 readiness が成功すること

## enabled:true に進む条件

`enabled:true` に進む前に、最低限以下を満たす必要がある。

- adapter の dry-run チェックが成功
- A/B preview の差分確認が完了
- 予測順位・買い目・期待値への影響範囲が明確
- 欠損 ID の扱いが安定
- default values の影響が許容範囲
- dashboard 表示に影響がない
- GitHub Actions が全成功
- rollback タグが存在する

## rollback 方針

問題が発生した場合は、以下のタグへ戻すことを検討する。

    history-feature-pre-enable-audit-stable
    history-feature-ab-preview-stable

また、`data/history_feature_config.json` の最上位 `enabled:false` を維持している限り、履歴特徴量は予測本体に反映されない。

## 結論

STEP137-C では、履歴特徴量を予測処理へ安全に渡すための adapter 方針を定義した。

現時点では設計のみであり、実装変更は行わない。

次の STEP137-D では、この設計に基づき、`enabled:false` のまま動作する adapter の dry-run 実装を検討する。

## adapter dry-run 実装完了記録

### 実施済みステップ

以下の adapter dry-run 関連ステップを完了した。

- STEP137-C: 履歴特徴量 prediction adapter 設計書作成
- STEP137-D: 履歴特徴量 prediction adapter dry-run 実装
- STEP137-E: adapter dry-run チェックを統合 readiness に追加
- STEP137-F: adapter preview JSON 出力
- STEP137-G: adapter preview JSON 検証スクリプト追加
- STEP137-H: adapter preview チェックを統合 readiness に追加

### 追加・更新された主なファイル

- `docs/history-feature-prediction-adapter-design.md`
- `scripts/history_feature_prediction_adapter.py`
- `scripts/check_history_feature_prediction_adapter.py`
- `scripts/check_history_database_readiness.py`
- `scripts/export_history_feature_adapter_preview.py`
- `docs/prediction_history_feature_adapter_preview.json`
- `scripts/check_history_feature_adapter_preview.py`

### 現在の安全状態

`data/history_feature_config.json` は引き続き `enabled:false` である。

そのため、履歴特徴量はまだ予測ロジック本体には反映されていない。

また、以下は変更していない。

- `docs/prediction.json`
- 予測スコア
- 予測順位
- 推奨買い目
- 期待値
- 予測ロジック本体

### adapter dry-run の役割

adapter dry-run は、既存予測 JSON 内の選手 ID 候補を確認し、履歴特徴量 CSV の `racer_id` と照合できるかを検証するための中間層である。

この adapter は、以下を行う。

- `racer_id`, `player_id`, `racerId`, `playerId`, `registration_number`, `toban`, `登番` の ID 正規化
- `scripts/history_feature_loader.py` を利用した履歴特徴量取得
- 欠損時 default values の利用
- `history_feature_preview` 用データの作成
- `affects_prediction_output:false` の維持
- `prediction_output_modified:false` の維持

### adapter preview JSON

adapter dry-run の結果は以下に出力した。

- `docs/prediction_history_feature_adapter_preview.json`

この JSON は確認用であり、既存の `docs/prediction.json` は変更しない。

preview JSON には以下の安全フラグを含める。

- `history_features_enabled:false`
- `affects_prediction_output:false`
- `prediction_output_modified:false`
- `prediction_json_modified:false`

### readiness 統合

`scripts/check_history_database_readiness.py` に以下を統合した。

- `scripts/check_history_feature_prediction_adapter.py`
- `scripts/check_history_feature_adapter_preview.py`

これにより、GitHub Actions の `Check History Database Readiness` で adapter dry-run と adapter preview の安全性を確認できる。

期待される主な出力は以下。

- `STEP 137-D CHECK: OK`
- `STEP 137-G CHECK: OK`
- `STEP 112 CHECK: OK`

### GitHub Actions 確認

以下の workflow に赤エラーがないことを確認した。

- `Check History Database Readiness`
- `Check Dashboard Final Readiness`
- `pages-build-deployment`

なお、`pages-build-deployment` で一時的に認証エラーが発生したが、再実行により解消した。

### enabled:true 前の注意点

`enabled:true` に進む前に、以下を確認する。

- adapter preview の matched / missing 状況
- 欠損 racer_id の扱い
- default values 利用時の影響
- 現行予測との差分
- 予測順位への影響
- 推奨買い目への影響
- 期待値への影響
- ダッシュボード表示崩れの有無
- GitHub Actions の全成功
- rollback タグの存在

### 結論

STEP137-C〜H により、履歴特徴量を予測ロジックへ接続する前段階の adapter dry-run 基盤が完成した。

現時点では `enabled:false` が維持されており、予測本体は未変更である。

次の段階では、adapter dry-run 状態に安定タグを付けたうえで、さらに予測本体へ接続する前の差分確認または dashboard 表示を検討する。
