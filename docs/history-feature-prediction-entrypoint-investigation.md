# 履歴特徴量 予測ロジック接続ポイント調査結果

## 概要

このドキュメントは、STEP137-A で実施した「予測ロジック接続前の実装入口調査」の結果を記録する。

目的は、履歴特徴量を将来的に予測処理へ接続する前に、既存の予測生成処理、JSON 出力、選手 ID、GitHub Actions の入口を把握することである。

現時点では、以下は実施していない。

- `data/history_feature_config.json` の `enabled:true` 化
- 予測スコア計算への履歴特徴量反映
- `docs/prediction.json` の構造変更
- 推奨買い目の変更
- 期待値計算の変更
- 本番予測ロジックの変更

現在も安全状態は以下である。

    {
      "enabled": false
    }

## STEP137-A 調査内容

STEP137-A では以下を調査した。

- 予測関連ファイル候補
- `docs/prediction.json` を作成・参照している可能性のある箇所
- 予測スコア、順位、確率、期待値、買い目関連キーワード
- `racer_id`, `player_id`, `racerId`, `playerId`, `registration_number`, `toban`, `登番`, `選手` の使用箇所
- GitHub Actions から実行される予測・ダッシュボード関連入口
- `docs/prediction.json` の構造

## 調査結果ファイル

STEP137-A の調査結果は、一時的に以下へ出力した。

    /tmp/history_feature_137a/candidate_files.txt
    /tmp/history_feature_137a/prediction_writers.txt
    /tmp/history_feature_137a/prediction_logic_keywords.txt
    /tmp/history_feature_137a/racer_id_usage.txt
    /tmp/history_feature_137a/workflow_entrypoints.txt
    /tmp/history_feature_137a/prediction_pretty.json

## 予測 JSON 生成元の確認方針

`docs/prediction.json` を直接生成しているスクリプト、または GitHub Actions 上で生成・更新している処理を特定する必要がある。

接続候補は以下のような箇所である。

- 予測スコア計算直後
- 選手ごとの予測情報を組み立てる箇所
- `docs/prediction.json` を書き出す直前
- A/B preview を生成する dry-run 処理

## 選手 ID の接続方針

履歴特徴量 CSV は `racer_id` をキーにしている。

既存予測 JSON 側で使用されている可能性のあるキーは以下である。

- `racer_id`
- `player_id`
- `racerId`
- `playerId`
- `registration_number`
- `toban`
- `登番`

実装前に、どのキーが最も安定して履歴特徴量と対応できるか確認する必要がある。

## 安全な接続方針

当面は以下の方針が安全である。

1. `enabled:false` のまま adapter を作る
2. 予測本体のスコアは変更しない
3. 履歴特徴量を別フィールドまたは preview にのみ付与する
4. A/B preview で差分を確認する
5. チェックと GitHub Actions を通す
6. 十分確認してから `enabled:true` を検討する

## enabled:true 前の注意点

`enabled:true` に進む前に、以下を必ず確認する。

- 既存予測順位との差分
- 推奨買い目の変化
- 期待値の変化
- 的中率・回収率への影響
- 欠損 racer_id の扱い
- デフォルト値利用時の影響
- JSON 構造変更による dashboard 影響
- GitHub Actions の全成功
- rollback タグの存在

## 関連する安全タグ

代表的な安全タグ:

    history-feature-ab-preview-stable
    history-feature-pre-enable-audit-stable

## 結論

STEP137-A は調査のみであり、予測本体への変更は行っていない。

現時点では `enabled:false` が維持されており、履歴特徴量は予測ロジックには未反映である。

次の STEP137-C では、調査結果をもとに、履歴特徴量を予測処理へ安全に渡すための adapter 設計を行う。
