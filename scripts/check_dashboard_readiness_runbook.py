#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "dashboard-readiness-runbook.md"
README = ROOT / "README.md"

REQUIRED_RUNBOOK_TOKENS = [
    "# ダッシュボード運用手順書",
    "日次更新または手動更新の流れ",
    "python scripts/ensure_prediction_json_dashboard_compat.py",
    "python scripts/check_recommendation_reasons.py",
    "python scripts/check_dashboard_final_readiness.py",
    "python scripts/check_readme_dashboard_readiness_doc.py",
    "python scripts/check_readme_dashboard_readiness_badge.py",
    "python scripts/check_dashboard_readiness_workflows.py",
    "python scripts/check_dashboard_readiness_outputs_ready.py",
    "STEP 80 CHECK: OK",
    "STEP 83 CHECK: OK",
    "STEP 84 CHECK: OK",
    "STEP 85 CHECK: OK",
    "STEP 87 CHECK: OK",
    "STEP 100 CHECK: OK",
    "GitHub Actions",
    "GitHub Pages",
    "pages-build-deployment",
    "git pull --rebase origin main",
    "git push origin main",
    "dashboard-readiness-stable",
]

REQUIRED_README_TOKENS = [
    "docs/dashboard-readiness-runbook.md",
]

CONFLICT_MARKERS = [
    "<<<<<<<",
    "=======",
    ">>>>>>>",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path: Path) -> str:
    if not path.exists():
        fail(f"required file not found: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    runbook_text = read_text(RUNBOOK)
    readme_text = read_text(README)

    for marker in CONFLICT_MARKERS:
        if marker in runbook_text:
            fail(f"conflict marker found in runbook: {marker}")
        if marker in readme_text:
            fail(f"conflict marker found in README: {marker}")

    missing_runbook = [
        token for token in REQUIRED_RUNBOOK_TOKENS
        if token not in runbook_text
    ]
    if missing_runbook:
        print("Missing runbook tokens:", file=sys.stderr)
        for token in missing_runbook:
            print(f"- {token}", file=sys.stderr)
        fail("dashboard readiness runbook is incomplete")

    missing_readme = [
        token for token in REQUIRED_README_TOKENS
        if token not in readme_text
    ]
    if missing_readme:
        print("Missing README tokens:", file=sys.stderr)
        for token in missing_readme:
            print(f"- {token}", file=sys.stderr)
        fail("README does not link to dashboard readiness runbook")

    print("Dashboard readiness runbook validation: OK")
    print("STEP 95 CHECK: OK")


if __name__ == "__main__":
    main()
