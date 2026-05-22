import json
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = [
    Path("docs/prediction.json"),
    Path("docs/prediction_run_summary.json"),
    Path(".github/workflows/make_prediction.yml"),
    Path("README.md"),
    Path("scripts/check_prediction_json_structure.py"),
    Path("scripts/check_prediction_run_summary_structure.py"),
    Path("scripts/check_prediction_outputs_consistency.py"),
    Path("scripts/check_make_prediction_workflow.py"),
    Path("scripts/check_readme_make_prediction_doc.py"),
    Path("scripts/check_readme_make_prediction_badge.py"),
    Path("scripts/check_make_prediction_schedule.py"),
]


def fail(errors):
    print("Make prediction outputs readiness errors:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def run(cmd):
    print("+", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    errors = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"missing required file: {path}")

    if errors:
        fail(errors)

    for json_path in [
        Path("docs/prediction.json"),
        Path("docs/prediction_run_summary.json"),
    ]:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON: {json_path}: {exc}")
            continue

        if not isinstance(data, dict):
            errors.append(f"{json_path} top-level must be object")

        if not data:
            errors.append(f"{json_path} must not be empty")

    workflow_text = Path(".github/workflows/make_prediction.yml").read_text(encoding="utf-8")
    readme_text = Path("README.md").read_text(encoding="utf-8")

    for label, text in [
        ("make_prediction.yml", workflow_text),
        ("README.md", readme_text),
    ]:
        if "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text:
            errors.append(f"{label} contains Git conflict markers")

    if errors:
        fail(errors)

    checks = [
        "scripts/check_prediction_json_structure.py",
        "scripts/check_prediction_run_summary_structure.py",
        "scripts/check_prediction_outputs_consistency.py",
        "scripts/check_make_prediction_workflow.py",
        "scripts/check_readme_make_prediction_doc.py",
        "scripts/check_readme_make_prediction_badge.py",
        "scripts/check_make_prediction_schedule.py",
    ]

    for script in checks:
        run([sys.executable, "-m", "py_compile", script])
        run([sys.executable, script])

    print("Make prediction outputs readiness validation: OK")
    print("STEP 70 CHECK: OK")


if __name__ == "__main__":
    main()
