# ダッシュボード運用手順書

この手順書は、ダッシュボード、予測 JSON、GitHub Actions、GitHub Pages を安定して運用するための標準手順をまとめたものです。

## 日次更新または手動更新の流れ

### 1. 最新の main ブランチを取得する

作業前に、リモートの最新状態を取り込みます。

```bash
git pull --rebase origin main

<!-- STEP95_RUNBOOK_REQUIRED_TOKENS -->

## 自動チェック用の必須確認項目

この節は、運用手順書が必要な内容を保持していることを自動確認するための項目です。

### 必須実行コマンド

```bash
python scripts/ensure_prediction_json_dashboard_compat.py
python scripts/check_recommendation_reasons.py
python scripts/check_dashboard_final_readiness.py
python scripts/check_readme_dashboard_readiness_doc.py
python scripts/check_readme_dashboard_readiness_badge.py
python scripts/check_dashboard_readiness_workflows.py
python scripts/check_dashboard_readiness_outputs_ready.py
```

### 必須成功メッセージ

```text
STEP 80 CHECK: OK
STEP 83 CHECK: OK
STEP 84 CHECK: OK
STEP 85 CHECK: OK
STEP 87 CHECK: OK
STEP 100 CHECK: OK
```

### GitHub Actions 確認対象

```text
pages-build-deployment
```

### push 手順

```bash
git push origin main
```

### 安定版 tag

```bash
git tag --list "dashboard-readiness-stable*"
```

dashboard-readiness-stable

