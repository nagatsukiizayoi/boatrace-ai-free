# ダッシュボード運用手順書

この手順書は、ダッシュボード、予測 JSON、GitHub Actions、GitHub Pages を安定して運用するための標準手順をまとめたものです。

## 日次更新または手動更新の流れ

### 1. 最新の main ブランチを取得する

作業前に、リモートの最新状態を取り込みます。

```bash
git pull --rebase origin main
