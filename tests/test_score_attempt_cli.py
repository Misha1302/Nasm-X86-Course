from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "score_attempt.py"
sys.path.insert(0, str(ROOT / "scripts"))

from assessment_engine import load_contract  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    contract = load_contract(ROOT)
    cp1 = contract["assessments"]["CP1"]
    full = {task: data["maximum"] for task, data in cp1["tasks"].items()}
    partial_task = next(task for task, data in cp1["tasks"].items() if data["maximum"] >= 2)

    with tempfile.TemporaryDirectory(prefix="nasm-score-cli-") as temp:
        root = Path(temp)
        attempt = root / "cp1.json"
        report = root / "report.json"

        attempt.write_text(json.dumps({"scores": full}), encoding="utf-8")
        passed = run("assessment", "CP1", str(attempt), "--json-output", str(report))
        require(passed.returncode == 0, passed.stdout + passed.stderr)
        require("CP1: PASS" in passed.stdout, "passing assessment was not rendered")
        require(json.loads(report.read_text(encoding="utf-8"))["passed"], "JSON PASS report is false")

        partial = dict(full)
        partial[partial_task] = 1
        attempt.write_text(json.dumps({"scores": partial}), encoding="utf-8")
        blocked = run("assessment", "CP1", str(attempt))
        require(blocked.returncode == 1, "partial checkpoint without a new variant passed")
        require(partial_task in blocked.stdout, "missing variant task was not reported")

        attempt.write_text(
            json.dumps({"scores": partial, "new_variants": [partial_task]}),
            encoding="utf-8",
        )
        repaired = run("assessment", "CP1", str(attempt))
        require(repaired.returncode == 0, repaired.stdout + repaired.stderr)

        attempt.write_text(json.dumps({"scores": full, "unknown": 1}), encoding="utf-8")
        unknown = run("assessment", "CP1", str(attempt))
        require(unknown.returncode == 2, "unknown input field was not rejected")
        require("INPUT_ERROR" in unknown.stderr, "unknown input diagnostic is missing")

        attempt.write_text("[]", encoding="utf-8")
        malformed = run("assessment", "CP1", str(attempt))
        require(malformed.returncode == 2, "non-object attempt input was not rejected")

        course = root / "course.json"
        course.write_text(json.dumps({"scores": {"UNKNOWN": {}}}), encoding="utf-8")
        course_result = run("course", str(course))
        require(course_result.returncode == 1, "invalid course readiness unexpectedly passed")
        require("unknown assessments" in course_result.stdout, "course diagnostic was not rendered")

    print("ASSESSMENT_CLI_PASS_FIXTURE=PASS")
    print("ASSESSMENT_CLI_PARTIAL_VARIANT=ENFORCED")
    print("ASSESSMENT_CLI_INPUT_SCHEMA=FAIL_CLOSED")
    print("ASSESSMENT_CLI_COURSE_READINESS=FAIL_CLOSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
