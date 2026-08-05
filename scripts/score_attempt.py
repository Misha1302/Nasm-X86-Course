#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assessment_engine import evaluate, evaluate_course, load_contract  # noqa: E402


class InputError(RuntimeError):
    pass


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError("attempt file must contain one JSON object")
    return value


def string_set(value: object, field: str) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise InputError(f"{field} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise InputError(f"{field} contains duplicate entries")
    return set(value)


def render_assessment(result: dict[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    lines = [
        f"{result['assessment']}: {status}",
        f"total: {result['total']}",
    ]
    if result["missing_skills"]:
        lines.append("missing skills: " + ", ".join(result["missing_skills"]))
    if result["missing_variants"]:
        lines.append("new variants required: " + ", ".join(result["missing_variants"]))
    if result["failures"]:
        lines.append("failures:")
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def render_course(result: dict[str, Any]) -> str:
    lines = [f"COURSE_READINESS: {'PASS' if result['ready'] else 'FAIL'}"]
    for failure in result["course_failures"]:
        lines.append(f"- {failure}")
    for assessment_id, decision in result["assessments"].items():
        lines.append(
            f"{assessment_id}: {'PASS' if decision['passed'] else 'FAIL'} "
            f"(total={decision['total']})"
        )
        for skill in decision["missing_skills"]:
            lines.append(f"  missing skill: {skill}")
        for task in decision["missing_variants"]:
            lines.append(f"  new variant required: {task}")
        for failure in decision["failures"]:
            lines.append(f"  - {failure}")
    return "\n".join(lines)


def write_json(path: str | None, value: dict[str, Any]) -> None:
    if path is None:
        return
    output = Path(path).resolve()
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"JSON_REPORT={output}")


def score_assessment(args: argparse.Namespace) -> int:
    payload = load_json_object(Path(args.input).resolve())
    allowed = {"scores", "new_variants"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise InputError("unknown top-level fields: " + ", ".join(unknown))
    if "scores" not in payload:
        raise InputError("missing required field: scores")

    contract = load_contract(ROOT)
    if args.assessment not in contract.get("assessments", {}):
        raise InputError(f"unknown assessment: {args.assessment}")

    decision = evaluate(
        args.assessment,
        payload["scores"],
        new_variants=string_set(payload.get("new_variants"), "new_variants"),
        contract=contract,
        readiness=args.readiness,
    )
    result = decision.to_dict()
    print(render_assessment(result))
    write_json(args.json_output, result)
    return 0 if decision.passed else 1


def normalize_course_variants(value: object) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InputError("variants must be an object mapping assessment IDs to string arrays")
    result: dict[str, list[str]] = {}
    for assessment_id, entries in value.items():
        if not isinstance(assessment_id, str) or not assessment_id:
            raise InputError("variants keys must be non-empty strings")
        normalized = sorted(string_set(entries, f"variants.{assessment_id}"))
        result[assessment_id] = normalized
    return result


def score_course(args: argparse.Namespace) -> int:
    payload = load_json_object(Path(args.input).resolve())
    allowed = {"scores", "variants"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise InputError("unknown top-level fields: " + ", ".join(unknown))
    if "scores" not in payload:
        raise InputError("missing required field: scores")

    contract = load_contract(ROOT)
    result = evaluate_course(
        payload["scores"],
        variants=normalize_course_variants(payload.get("variants")),
        contract=contract,
    )
    print(render_course(result))
    write_json(args.json_output, result)
    return 0 if result["ready"] else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Score a NASM course checkpoint, final attempt, or complete course readiness."
    )
    sub = root.add_subparsers(dest="command", required=True)

    assessment = sub.add_parser("assessment", help="score one checkpoint or FINAL")
    assessment.add_argument("assessment", help="assessment ID such as CP2 or FINAL")
    assessment.add_argument("input", help="JSON file with scores and optional new_variants")
    assessment.add_argument(
        "--readiness",
        action="store_true",
        help="require new variants for partial FINAL evidence as course readiness does",
    )
    assessment.add_argument("--json-output", help="write the complete machine-readable result")
    assessment.set_defaults(handler=score_assessment)

    course = sub.add_parser("course", help="score CP1..CP6 and FINAL together")
    course.add_argument("input", help="JSON file with scores and optional variants")
    course.add_argument("--json-output", help="write the complete machine-readable result")
    course.set_defaults(handler=score_course)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InputError as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
