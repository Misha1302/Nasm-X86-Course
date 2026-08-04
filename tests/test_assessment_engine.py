from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assessment_engine import evaluate, evaluate_course, load_contract  # noqa: E402
from assessment_schema import ValidationError, validate_schema  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    contract = load_contract(ROOT)
    assessment = contract["assessments"]["CP1"]
    task = next(iter(assessment["tasks"]))

    malformed = ["2", None, 1.5, True, -1, assessment["tasks"][task]["maximum"] + 1]
    for value in malformed:
        decision = evaluate("CP1", {task: value}, contract=contract)
        require(not decision.passed, f"ASSESS-ENGINE-MALFORMED: {value!r} unexpectedly passed")
        require(isinstance(decision.total, int), f"ASSESS-ENGINE-TOTAL: {value!r} produced non-int total")
        require(decision.total == 0, f"ASSESS-ENGINE-FAIL-CLOSED: {value!r} contributed {decision.total}")
        require(any("score" in failure for failure in decision.failures), f"ASSESS-ENGINE-DIAGNOSTIC: {value!r}")

    non_mapping = evaluate("CP1", None, contract=contract)
    require(not non_mapping.passed, "ASSESS-ENGINE-MAPPING: None unexpectedly passed")
    require(non_mapping.total == 0, "ASSESS-ENGINE-MAPPING: invalid score container contributed points")
    require(any("expected a mapping" in failure for failure in non_mapping.failures), "ASSESS-ENGINE-MAPPING: diagnostic missing")

    full = {name: data["maximum"] for name, data in assessment["tasks"].items()}
    full[task] = 1
    partial = evaluate("CP1", full, contract=contract)
    require(task in partial.missing_variants, "ASSESS-ENGINE-PARTIAL: partial score did not require variant")
    completed = evaluate("CP1", full, new_variants={task}, contract=contract)
    require(task not in completed.missing_variants, "ASSESS-ENGINE-PARTIAL: supplied variant was ignored")

    invalid_course = evaluate_course(None, contract=contract)
    require(not invalid_course["ready"], "ASSESS-COURSE-MAPPING: None unexpectedly ready")
    require(
        any("all_scores: expected a mapping" in failure for failure in invalid_course["course_failures"]),
        "ASSESS-COURSE-MAPPING: top-level diagnostic missing",
    )

    unknown_course = evaluate_course({"UNKNOWN": {}}, contract=contract)
    require(not unknown_course["ready"], "ASSESS-COURSE-UNKNOWN: unknown assessment was ignored")
    require(
        any("unknown assessments" in failure for failure in unknown_course["course_failures"]),
        "ASSESS-COURSE-UNKNOWN: diagnostic missing",
    )

    invalid_variants = evaluate_course({}, variants=1, contract=contract)
    require(not invalid_variants["ready"], "ASSESS-COURSE-VARIANTS: malformed variants unexpectedly ready")
    require(
        any("variants: expected a mapping" in failure for failure in invalid_variants["course_failures"]),
        "ASSESS-COURSE-VARIANTS: diagnostic missing",
    )

    kind_drift = copy.deepcopy(contract)
    kind_drift["assessments"]["CP1"]["kind"] = "final"
    try:
        validate_schema(kind_drift)
    except ValidationError as exc:
        require("ASSESS-KIND" in str(exc), f"ASSESS-KIND-PROBE: wrong diagnostic: {exc}")
    else:
        raise RuntimeError("ASSESS-KIND-PROBE: CP1 kind drift was accepted")

    print(f"ASSESSMENT_ENGINE_MALFORMED_CASES={len(malformed) + 1}")
    print("ASSESSMENT_COURSE_FAIL_CLOSED=PASS")
    print("ASSESSMENT_KIND_OWNERSHIP=PASS")
    print("ASSessment_ENGINE_FAIL_CLOSED=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
