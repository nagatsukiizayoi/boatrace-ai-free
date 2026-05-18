# Production Database Design

## 概要

このドキュメントは、競艇予想システムを本番運用に近づけるための DB 設計方針をまとめるものです。

現在の DB は、サンプル CSV を取り込み、prediction.json を生成し、ダッシュボード表示と GitHub Actions 検証まで行える状態です。

今後は、実レースデータ、選手情報、モーター情報、展示情報、オッズ時系列、予測履歴、的中結果、回収率分析を保存できる構造へ拡張します。

## 現在の標準 DB 構築方法

python scripts/build_database.py --reset
python scripts/build_database.py --reset --with-sample-data
python scripts/init_db.py --reset

## 統合スキーマ確認

python scripts/check_integrated_schema.py

期待結果: STEP 104 CHECK: OK

## 本番DBで管理したいデータ

### 1. レース基本情報
- 開催日
- 場コード
- 場名
- レース番号
- 締切予定時刻
- 天候、風速、波高、水温、気温

候補テーブル: races, venues, race_conditions

### 2. 選手マスタ
- 登録番号
- 選手名
- 支部
- 級別
- 全国勝率
- 当地勝率

候補テーブル: racers, racer_stats_snapshots

### 3. 出走表・枠番情報
- race_id
- 枠番
- 登録番号
- モーター番号
- ボート番号
- 展示タイム

候補テーブル: race_entries, entry_conditions

### 4. オッズ時系列
- race_id
- bet_type
- ticket
- odds
- 取得時刻
- 人気順位

候補テーブル: odds_snapshots, odds_movements

### 5. 予測実行履歴
- run_key
- model_name
- model_version
- target_date
- 実行時刻
- 品質スコア

候補テーブル: prediction_runs, prediction_run_metrics

### 6. 予測買い目
- prediction_id
- race_id
- bet_type
- ticket
- confidence
- odds
- expected_value
- recommendation_reason

候補テーブル: predictions, prediction_tickets, prediction_ticket_reasons

### 7. レース結果・払戻
- 着順
- 決まり手
- 的中組番
- 払戻金
- 人気

候補テーブル: race_results, payouts

### 8. 的中判定・回収率分析
- 的中有無
- 購入金額
- 払戻金
- 回収率
- モデル別成績
- value_grade 別成績

候補テーブル: bet_results, return_rate_summaries, model_performance_summaries

## 拡張方針

1. 既存テーブルを壊さない
2. 予測と結果を分離する
3. 時系列データは snapshot として保存する
4. モデル評価に必要な情報を残す

## 優先して追加する候補テーブル

1. prediction_runs
2. race_results
3. payouts
4. bet_results
5. return_rate_summaries
6. racer_stats_snapshots
7. motor_stats_snapshots
8. exhibition_records
9. odds_movements

## STEP108 の完了条件

- docs/dev/production_database_design.md が存在する
- 本番DBで管理したいデータ分類が整理されている
- 追加候補テーブルが明記されている
- 既存スキーマを壊さない方針が明記されている
- GitHub に push 済み

## 次のステップ

STEP109 では、最初の本番向け追加テーブルとして prediction_runs を設計・追加します。
