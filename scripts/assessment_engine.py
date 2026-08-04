from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Decision:
    assessment: str
    passed: bool
    total: int
    failures: tuple[str, ...]
    missing_skills: tuple[str, ...]
    missing_variants: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / "scripts" / "assessment_contract.json").read_text(encoding="utf-8"))


def _normalize_scores(
    assessment: Mapping[str, Any],
    scores: object,
    failures: list[str],
) -> dict[str, int]:
    """Return a fail-closed integer score map."""

    if not isinstance(scores, Mapping):
        failures.append(f"scores: expected a mapping, got {type(scores).__name__}")
        raw_scores: Mapping[object, object] = {}
    else:
        raw_scores = scores

    expected = set(assessment["tasks"])
    unknown = [key for key in raw_scores if key not in expected]
    if unknown:
        rendered = ", ".join(sorted((repr(key) for key in unknown)))
        failures.append("unknown tasks: " + rendered)

    normalized: dict[str, int] = {}
    for task, task_data in assessment["tasks"].items():
        raw = raw_scores.get(task, 0)
        maximum = task_data["maximum"]
        valid = isinstance(raw, int) and not isinstance(raw, bool) and 0 <= raw <= maximum
        if not valid:
            failures.append(f"{task}: score {raw!r} outside integer range 0..{maximum}")
            normalized[task] = 0
        else:
            normalized[task] = raw
    return normalized


def evaluate(
    assessment_id: str,
    scores: object,
    *,
    new_variants: set[str] | None = None,
    contract: dict[str, Any] | None = None,
    readiness: bool = False,
) -> Decision:
    contract = contract or load_contract()
    assessment = contract["assessments"][assessment_id]
    variants = new_variants or set()
    failures: list[str] = []
    missing_skills: list[str] = []
    missing_variants: list[str] = []

    normalized = _normalize_scores(assessment, scores, failures)

    total = sum(normalized.values())
    if total < assessment["threshold"]:
        failures.append(f'total {total} < threshold {assessment["threshold"]}')

    for block, block_data in assessment["block_minimums"].items():
        got = sum(normalized[task] for task in block_data["tasks"])
        if got < block_data["minimum"]:
            failures.append(f'block {block}: {got} < {block_data["minimum"]}')

    for rule in assessment["critical_task_rules"]:
        got = normalized[rule["task"]]
        if got < rule["minimum_score"]:
            failures.append(f'critical {rule["task"]}: {got} < {rule["minimum_score"]}')

    for skill, skill_data in assessment["skills"].items():
        if not skill_data.get("mandatory", False):
            continue
        evidence = sum(
            normalized[evidence_rule["task"]] >= evidence_rule["minimum_score"]
            for evidence_rule in skill_data["acceptable_evidence"]
        )
        if evidence < skill_data["minimum_evidence"]:
            missing_skills.append(skill)
            failures.append(
                f'mandatory skill {skill}: evidence {evidence} < {skill_data["minimum_evidence"]}'
            )

    require_variants = assessment["kind"] == "checkpoint" or readiness
    if require_variants:
        for task, task_data in assessment["tasks"].items():
            score = normalized[task]
            if 0 < score < task_data["maximum"] and task not in variants:
                missing_variants.append(task)
                suffix = (
                    "partial score requires a new variant"
                    if assessment["kind"] == "checkpoint"
                    else "partial final evidence requires a new variant for full readiness"
                )
                failures.append(f"{task}: {suffix}")

    return Decision(
        assessment_id,
        not failures,
        total,
        tuple(failures),
        tuple(missing_skills),
        tuple(missing_variants),
    )


def _normalize_variant_map(
    variants: object,
    required: set[str],
    failures: list[str],
) -> dict[str, set[str]]:
    if variants is None:
        return {}
    if not isinstance(variants, Mapping):
        failures.append(f"variants: expected a mapping, got {type(variants).__name__}")
        return {}

    unknown = [key for key in variants if key not in required]
    if unknown:
        failures.append("unknown variant assessments: " + ", ".join(sorted(repr(key) for key in unknown)))

    normalized: dict[str, set[str]] = {}
    for assessment_id in required:
        raw = variants.get(assessment_id, set())
        if isinstance(raw, (set, frozenset, list, tuple)) and all(isinstance(item, str) for item in raw):
            normalized[assessment_id] = set(raw)
        else:
            failures.append(
                f"variants[{assessment_id!r}]: expected a string collection, got {type(raw).__name__}"
            )
            normalized[assessment_id] = set()
    return normalized


def evaluate_course(
    all_scores: object,
    *,
    variants: object = None,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or load_contract()
    required_order = contract["course_readiness"]["required_assessments"]
    required = set(required_order)
    course_failures: list[str] = []

    if isinstance(all_scores, Mapping):
        raw_scores: Mapping[object, object] = all_scores
        unknown = [key for key in raw_scores if key not in required]
        if unknown:
            course_failures.append(
                "unknown assessments: " + ", ".join(sorted(repr(key) for key in unknown))
            )
    else:
        course_failures.append(f"all_scores: expected a mapping, got {type(all_scores).__name__}")
        raw_scores = {}

    normalized_variants = _normalize_variant_map(variants, required, course_failures)
    decisions = {
        assessment_id: evaluate(
            assessment_id,
            raw_scores.get(assessment_id, None if not isinstance(all_scores, Mapping) else {}),
            new_variants=normalized_variants.get(assessment_id, set()),
            contract=contract,
            readiness=True,
        )
        for assessment_id in required_order
    }
    return {
        "ready": not course_failures and all(decision.passed for decision in decisions.values()),
        "course_failures": tuple(course_failures),
        "assessments": {key: value.to_dict() for key, value in decisions.items()},
    }
