# Legacy Schema Patch Scripts

このプロジェクトでは、STEP104 で `db/schema.sql` に後付けパッチ内容を統合しました。

そのため、通常の DB 構築では以下の旧パッチスクリプトは使用しません。

- `scripts/patch_step68_schema.py`
- `scripts/patch_step78_ticket_schema.py`

## 現在の標準 DB 構築方法

通常は以下を使用します。

```bash
python scripts/build_database.py --reset
```

サンプルデータ込みで構築する場合：

```bash
python scripts/build_database.py --reset --with-sample-data
```

これは、開発・テスト・GitHub Actions などで、DB構築後にサンプルCSVも投入して動作確認したい場合に使用します。

スキーマのみ初期化する場合：

```bash
python scripts/init_db.py --reset
```

## 統合スキーマの確認

`db/schema.sql` だけで必要なテーブル・カラムが揃うことは、以下で確認します。

```bash
python scripts/check_integrated_schema.py
```

成功時：

```text
STEP 104 CHECK: OK
```

## 旧パッチスクリプトの扱い

以下のスクリプトは legacy 扱いです。

```text
scripts/patch_step68_schema.py
scripts/patch_step78_ticket_schema.py
```

これらは以下の目的でのみ残しています。

- 過去の STEP との互換性確認
- 古い DB ファイルを手動修復する場合
- 統合前スキーマとの差分確認
- 緊急時の復旧作業

## 注意

通常の workflow やフルパイプラインでは使用しません。

新規開発では `db/schema.sql` を更新し、必要に応じて以下を実行してください。

```bash
python scripts/check_integrated_schema.py
python scripts/run_full_prediction_pipeline.py
python scripts/check_dashboard_final_readiness.py
```

## 関連 STEP

- STEP104: 後付けパッチを正式スキーマへ統合
- STEP105: 統合スキーマを GitHub Actions で自動チェック
- STEP106: 通常フローから旧パッチ呼び出しを削除
- STEP107: 旧パッチを legacy 扱いとして明示
