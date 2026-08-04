from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

from assessment_engine import evaluate, load_contract
from assessment_schema import (
    PARTIAL_CONDITION,
    REQUIRED_ASSESSMENTS,
    ValidationError,
    require,
    validate_schema,
)
from evidence_provenance import digest_paths

ROOT = Path(__file__).resolve().parents[1]


def enumerate_checkpoint(contract: dict[str, Any], assessment_id: str) -> int:
    assessment = contract["assessments"][assessment_id]
    tasks = list(assessment["tasks"])
    ranges = [range(assessment["tasks"][task]["maximum"] + 1) for task in tasks]
    expected = math.prod(len(domain) for domain in ranges)
    visited = 0
    for values in itertools.product(*ranges):
        visited += 1
        scores = dict(zip(tasks, values))
        variants = {
            task
            for task, score in scores.items()
            if 0 < score < assessment["tasks"][task]["maximum"]
        }
        decision = evaluate(assessment_id, scores, new_variants=variants, contract=contract)
        if decision.passed:
            for skill, skill_data in assessment["skills"].items():
                evidence = sum(
                    scores[evidence_rule["task"]] >= evidence_rule["minimum_score"]
                    for evidence_rule in skill_data["acceptable_evidence"]
                )
                require(
                    evidence >= skill_data["minimum_evidence"],
                    f"ASSESS-FALSE-PASS {assessment_id}: {skill} missing for {scores}",
                )
    require(
        visited == expected,
        f"ASSESS-DOMAIN-COVERAGE {assessment_id}: visited {visited}, expected {expected}",
    )
    return visited


def exhaustive_checkpoints(contract: dict[str, Any]) -> dict[str, int]:
    return {assessment_id: enumerate_checkpoint(contract, assessment_id) for assessment_id in REQUIRED_ASSESSMENTS[:-1]}


def monotone_final_constraint_proof(contract: dict[str, Any]) -> dict[str, Any]:
    """Exact finite proof for each missing mandatory FINAL skill.

    PASS predicates are monotone in scores once partial-evidence variants are
    supplied. A missing-skill witness therefore also exists with unrelated tasks
    at maximum. Only the bounded domains of that skill's evidence tasks need to
    be enumerated.
    """

    assessment = contract["assessments"]["FINAL"]
    checked = 0
    witnesses: list[dict[str, Any]] = []
    for skill, skill_data in assessment["skills"].items():
        evidence_tasks = sorted({rule["task"] for rule in skill_data["acceptable_evidence"]})
        ranges = [range(assessment["tasks"][task]["maximum"] + 1) for task in evidence_tasks]
        for values in itertools.product(*ranges):
            scores = {task: task_data["maximum"] for task, task_data in assessment["tasks"].items()}
            scores.update(dict(zip(evidence_tasks, values)))
            evidence = sum(
                scores[rule["task"]] >= rule["minimum_score"]
                for rule in skill_data["acceptable_evidence"]
            )
            if evidence >= skill_data["minimum_evidence"]:
                continue
            checked += 1
            decision = evaluate(
                "FINAL",
                scores,
                new_variants=set(assessment["tasks"]),
                contract=contract,
                readiness=True,
            )
            if decision.passed:
                witnesses.append({"skill": skill, "scores": scores})
    require(not witnesses, f"ASSESS-FINAL-FALSE-PASS: {witnesses[:1]}")
    return {
        "solver": "monotone bounded constraint enumeration",
        "assignments_checked": checked,
        "witnesses": witnesses,
    }


def regression_fixtures(contract: dict[str, Any]) -> dict[str, Any]:
    fixtures = json.loads((ROOT / "tests" / "fixtures" / "scoring.json").read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    for fixture in fixtures:
        decision = evaluate(
            fixture["assessment"],
            fixture["scores"],
            new_variants=set(fixture.get("new_variants", [])),
            contract=contract,
            readiness=fixture.get("readiness", False),
        )
        require(
            decision.passed == fixture["expected_pass"],
            f"ASSESS-REGRESSION {fixture['id']}: expected {fixture['expected_pass']}, got {decision.passed}; {decision.failures}",
        )
        if "expected_missing_skill" in fixture:
            require(
                fixture["expected_missing_skill"] in decision.missing_skills,
                f"ASSESS-REGRESSION {fixture['id']}: expected missing skill {fixture['expected_missing_skill']}; got {decision.missing_skills}",
            )
        results[fixture["id"]] = decision.to_dict()
    return results


def schema_regression_probes(contract: dict[str, Any]) -> dict[str, str | int]:
    assessment_id = "CP1"

    duplicate = copy.deepcopy(contract)
    skill = next(iter(duplicate["assessments"][assessment_id]["skills"]))
    duplicate["assessments"][assessment_id]["skills"][skill]["acceptable_evidence"].append(
        copy.deepcopy(duplicate["assessments"][assessment_id]["skills"][skill]["acceptable_evidence"][0])
    )
    try:
        validate_schema(duplicate)
    except ValidationError as exc:
        require("ASSESS-EVIDENCE-DUPLICATE" in str(exc), f"ASSESS-SCHEMA-PROBE: wrong duplicate diagnostic: {exc}")
    else:
        raise ValidationError("ASSESS-SCHEMA-PROBE: duplicate evidence was accepted")

    asymmetric = copy.deepcopy(contract)
    skill = next(iter(asymmetric["assessments"][assessment_id]["skills"]))
    foreign_task = next(
        task
        for task, task_data in asymmetric["assessments"][assessment_id]["tasks"].items()
        if skill not in task_data["skills"]
    )
    asymmetric["assessments"][assessment_id]["skills"][skill]["acceptable_evidence"].append(
        {"task": foreign_task, "minimum_score": 1}
    )
    try:
        validate_schema(asymmetric)
    except ValidationError as exc:
        require("ASSESS-EVIDENCE-BIDIRECTIONAL" in str(exc), f"ASSESS-SCHEMA-PROBE: wrong ownership diagnostic: {exc}")
    else:
        raise ValidationError("ASSESS-SCHEMA-PROBE: asymmetric evidence was accepted")

    orphan = copy.deepcopy(contract)
    orphan["declared_outcomes"]["orphan_outcome"] = {
        "mandatory": True,
        "owner_assessment": assessment_id,
    }
    try:
        validate_schema(orphan)
    except ValidationError as exc:
        require("ASSESS-OUTCOME-COVERAGE" in str(exc), f"ASSESS-SCHEMA-PROBE: wrong orphan diagnostic: {exc}")
    else:
        raise ValidationError("ASSESS-SCHEMA-PROBE: orphan declared outcome was accepted")

    owner_drift = copy.deepcopy(contract)
    owner_key = next(key for key, data in owner_drift["declared_outcomes"].items() if data["owner_assessment"] == assessment_id)
    owner_drift["declared_outcomes"][owner_key]["owner_assessment"] = "FINAL"
    try:
        validate_schema(owner_drift)
    except ValidationError as exc:
        require("ASSESS-OUTCOME-OWNER" in str(exc), f"ASSESS-SCHEMA-PROBE: wrong owner diagnostic: {exc}")
    else:
        raise ValidationError("ASSESS-SCHEMA-PROBE: outcome owner drift was accepted")

    expanded = copy.deepcopy(contract)
    task = next(iter(expanded["assessments"][assessment_id]["tasks"]))
    expanded["assessments"][assessment_id]["tasks"][task]["maximum"] += 1
    expanded["assessments"][assessment_id]["maximum"] += 1
    expanded["assessments"][assessment_id]["score_domain"] = [0, 1, 2, 3]
    expanded["assessments"][assessment_id]["partial_error_rule"] = {
        "condition": PARTIAL_CONDITION,
        "requires_new_variant": True,
    }
    validate_schema(expanded)
    count = enumerate_checkpoint(expanded, assessment_id)
    expected = math.prod(
        task_data["maximum"] + 1
        for task_data in expanded["assessments"][assessment_id]["tasks"].values()
    )
    require(count == expected, f"ASSESS-DOMAIN-PROBE: visited {count}, expected {expected}")

    return {
        "duplicate_evidence": "REJECTED",
        "asymmetric_evidence": "REJECTED",
        "orphan_declared_outcome": "REJECTED",
        "outcome_owner_drift": "REJECTED",
        "dynamic_domain_assignments": count,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    unknown = [argument for argument in arguments if argument != "--schema-only"]
    if unknown:
        print(f"ASSESS-CLI: unsupported arguments: {unknown}", file=sys.stderr)
        return 2
    schema_only = "--schema-only" in arguments

    try:
        contract = load_contract(ROOT)
        validate_schema(contract)
        if schema_only:
            print("ASSESSMENT_SCHEMA=PASS")
            return 0
        probes = schema_regression_probes(contract)
        exhaustive = exhaustive_checkpoints(contract)
        final_proof = monotone_final_constraint_proof(contract)
        regressions = regression_fixtures(contract)
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    source_digest = digest_paths(
        ROOT,
        [
            "scripts/assessment_contract.json",
            "scripts/assessment_engine.py",
            "scripts/validate_assessment.py",
            "scripts/assessment_schema.py",
            "scripts/evidence_provenance.py",
            "tests/fixtures/scoring.json",
        ],
    )
    report = {
        "schema_version": "3.0",
        "source_digest": source_digest,
        "schema": "PASS",
        "schema_regression_probes": probes,
        "checkpoint_score_domains": {
            assessment_id: {
                task: task_data["maximum"]
                for task, task_data in contract["assessments"][assessment_id]["tasks"].items()
            }
            for assessment_id in REQUIRED_ASSESSMENTS[:-1]
        },
        "exhaustive_checkpoint_assignments": exhaustive,
        "final_constraint_proof": final_proof,
        "regressions": regressions,
    }
    (ROOT / "ASSESSMENT_PROOF.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("ASSESSMENT_SCHEMA=PASS")
    print("ASSESSMENT_SCHEMA_PROBES=PASS")
    print("CHECKPOINT_EXHAUSTIVE=PASS " + " ".join(f"{key}:{value}" for key, value in exhaustive.items()))
    print(f"FINAL_CONSTRAINT_PROOF=PASS checked={final_proof['assignments_checked']}")
    print(f"SCORING_REGRESSIONS=PASS count={len(regressions)}")
    print(f"ASSESSMENT_SOURCE_DIGEST={source_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
