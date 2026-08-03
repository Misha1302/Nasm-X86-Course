from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

from assessment_engine import evaluate, load_contract
from evidence_provenance import digest_paths

ROOT = Path(__file__).resolve().parents[1]


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_schema(c: dict[str, Any]) -> None:
    require(c.get("schema_version") == "2.0", "ASSESS-SCHEMA: schema_version must be 2.0")
    require(c.get("canonical_owner") == "scripts/assessment_contract.json", "ASSESS-OWNER: canonical owner changed")
    required = ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6", "FINAL"]
    require(
        c["course_readiness"]["required_assessments"] == required,
        "ASSESS-READINESS: readiness must compose CP1..CP6 + FINAL",
    )
    require(c["day10"]["mandatory_sessions"] == ["10A", "10B", "10C", "10D", "10E"], "ASSESS-DAY10: mandatory core must be 10A..10E")
    require(c["day10"]["optional_sessions"] == ["10F"], "ASSESS-DAY10-BONUS: 10F must remain optional")
    require(set(c["day10"]["bonus_only"]) == {"10F", "01-16"}, "ASSESS-BONUS: 10F and 01-16 must be bonus-only")
    fb = c["assessments"]["FINAL"]["bonus_rules"]
    require(fb.get("included_in_maximum") is False, "ASSESS-BONUS: bonus tasks must not be included in the final maximum")
    require(fb.get("bonus_can_compensate_mandatory") is False, "ASSESS-BONUS: bonus must not compensate mandatory evidence")

    outcome_owner = c["declared_outcomes"]
    for aid, assessment in c["assessments"].items():
        tasks = assessment["tasks"]
        require(tasks, f"ASSESS-TASKS {aid}: assessment has no tasks")
        for task, td in tasks.items():
            maximum = td.get("maximum")
            require(
                isinstance(maximum, int) and not isinstance(maximum, bool) and maximum >= 1,
                f"ASSESS-TASK-MAXIMUM {aid}/{task}: maximum must be a positive integer",
            )
        require(
            sum(t["maximum"] for t in tasks.values()) == assessment["maximum"],
            f"ASSESS-MAXIMUM {aid}: task maxima do not sum to assessment maximum",
        )
        require(0 < assessment["threshold"] <= assessment["maximum"], f"ASSESS-THRESHOLD {aid}: invalid threshold")

        for block, bd in assessment["block_minimums"].items():
            require(set(bd["tasks"]) <= set(tasks), f"ASSESS-BLOCK {aid}/{block}: unknown task")
            require(
                0 <= bd["minimum"] <= sum(tasks[t]["maximum"] for t in bd["tasks"]),
                f"ASSESS-BLOCK {aid}/{block}: impossible minimum",
            )

        for rule in assessment["critical_task_rules"]:
            require(rule["task"] in tasks, f"ASSESS-CRITICAL {aid}: unknown task {rule['task']}")
            require(
                1 <= rule["minimum_score"] <= tasks[rule["task"]]["maximum"],
                f"ASSESS-CRITICAL {aid}/{rule['task']}: invalid minimum",
            )

        for skill, sd in assessment["skills"].items():
            key = skill if aid != "FINAL" else "final." + skill
            require(key in outcome_owner and outcome_owner[key]["mandatory"], f"ASSESS-OUTCOME {aid}/{skill}: mandatory outcome disappeared")
            require(sd.get("mandatory") is True, f"ASSESS-MANDATORY {aid}/{skill}: outcome is no longer mandatory")
            evidence = sd.get("acceptable_evidence")
            require(evidence, f"ASSESS-EVIDENCE {aid}/{skill}: no acceptable evidence")

            seen: set[tuple[str, int]] = set()
            for ev in evidence:
                task = ev["task"]
                minimum = ev["minimum_score"]
                require(task in tasks, f"ASSESS-EVIDENCE {aid}/{skill}: unknown task {task}")
                require(1 <= minimum <= tasks[task]["maximum"], f"ASSESS-EVIDENCE {aid}/{skill}: invalid minimum")
                signature = (task, minimum)
                require(signature not in seen, f"ASSESS-EVIDENCE-DUPLICATE {aid}/{skill}: duplicate {task}@{minimum}")
                seen.add(signature)
                require(
                    skill in tasks[task].get("skills", []),
                    f"ASSESS-EVIDENCE-BIDIRECTIONAL {aid}/{skill}: {task} accepts the skill but task.skills does not declare it",
                )
            minimum_evidence = sd.get("minimum_evidence")
            require(
                isinstance(minimum_evidence, int)
                and not isinstance(minimum_evidence, bool)
                and 1 <= minimum_evidence <= len(seen),
                f"ASSESS-EVIDENCE-MINIMUM {aid}/{skill}: minimum_evidence is invalid",
            )

        for task, td in tasks.items():
            mapped = td.get("skills")
            require(mapped, f"ASSESS-TASK-SKILL {aid}/{task}: task has no atomic skill mapping")
            require(len(mapped) == len(set(mapped)), f"ASSESS-TASK-SKILL-DUPLICATE {aid}/{task}: duplicate skill mapping")
            for skill in mapped:
                require(skill in assessment["skills"], f"ASSESS-TASK-SKILL {aid}/{task}: unknown skill {skill}")
                evidence_tasks = {ev["task"] for ev in assessment["skills"][skill]["acceptable_evidence"]}
                require(
                    task in evidence_tasks,
                    f"ASSESS-EVIDENCE-BIDIRECTIONAL {aid}/{task}: mapped skill {skill} does not accept evidence from this task",
                )


def enumerate_checkpoint(c: dict[str, Any], aid: str) -> int:
    assessment = c["assessments"][aid]
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
        decision = evaluate(aid, scores, new_variants=variants, contract=c)
        if decision.passed:
            for skill, sd in assessment["skills"].items():
                evidence = sum(scores[e["task"]] >= e["minimum_score"] for e in sd["acceptable_evidence"])
                require(evidence >= sd["minimum_evidence"], f"ASSESS-FALSE-PASS {aid}: {skill} missing for {scores}")
    require(visited == expected, f"ASSESS-DOMAIN-COVERAGE {aid}: visited {visited}, expected {expected}")
    return visited


def exhaustive_checkpoints(c: dict[str, Any]) -> dict[str, int]:
    return {aid: enumerate_checkpoint(c, aid) for aid in [f"CP{i}" for i in range(1, 7)]}


def monotone_final_constraint_proof(c: dict[str, Any]) -> dict[str, Any]:
    """Exact finite proof for each missing mandatory FINAL skill.

    PASS predicates are monotone in scores once partial-evidence variants are supplied.
    Therefore a missing-skill witness, if one exists, also exists with all unrelated
    tasks at maximum. We enumerate the bounded domains of the skill's evidence tasks.
    """

    assessment = c["assessments"]["FINAL"]
    checked = 0
    witnesses: list[dict[str, Any]] = []
    for skill, sd in assessment["skills"].items():
        evidence_tasks = sorted({ev["task"] for ev in sd["acceptable_evidence"]})
        ranges = [range(assessment["tasks"][task]["maximum"] + 1) for task in evidence_tasks]
        for values in itertools.product(*ranges):
            scores = {task: td["maximum"] for task, td in assessment["tasks"].items()}
            scores.update(dict(zip(evidence_tasks, values)))
            evidence = sum(scores[ev["task"]] >= ev["minimum_score"] for ev in sd["acceptable_evidence"])
            if evidence >= sd["minimum_evidence"]:
                continue
            checked += 1
            decision = evaluate(
                "FINAL",
                scores,
                new_variants=set(assessment["tasks"]),
                contract=c,
                readiness=True,
            )
            if decision.passed:
                witnesses.append({"skill": skill, "scores": scores})
    require(not witnesses, f"ASSESS-FINAL-FALSE-PASS: {witnesses[:1]}")
    return {"solver": "monotone bounded constraint enumeration", "assignments_checked": checked, "witnesses": witnesses}


def regression_fixtures(c: dict[str, Any]) -> dict[str, Any]:
    fixtures = json.loads((ROOT / "tests/fixtures/scoring.json").read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    for fixture in fixtures:
        decision = evaluate(
            fixture["assessment"],
            fixture["scores"],
            new_variants=set(fixture.get("new_variants", [])),
            contract=c,
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


def schema_regression_probes(c: dict[str, Any]) -> dict[str, str | int]:
    # Duplicate evidence must never satisfy minimum_evidence twice.
    duplicate = copy.deepcopy(c)
    aid = "CP1"
    skill = next(iter(duplicate["assessments"][aid]["skills"]))
    duplicate["assessments"][aid]["skills"][skill]["acceptable_evidence"].append(
        copy.deepcopy(duplicate["assessments"][aid]["skills"][skill]["acceptable_evidence"][0])
    )
    try:
        validate_schema(duplicate)
    except ValidationError as exc:
        require("ASSESS-EVIDENCE-DUPLICATE" in str(exc), f"ASSESS-SCHEMA-PROBE: wrong duplicate diagnostic: {exc}")
    else:
        raise ValidationError("ASSESS-SCHEMA-PROBE: duplicate evidence was accepted")

    # Evidence ownership must be declared in both directions.
    asymmetric = copy.deepcopy(c)
    skill = next(iter(asymmetric["assessments"][aid]["skills"]))
    foreign_task = next(
        task
        for task, td in asymmetric["assessments"][aid]["tasks"].items()
        if skill not in td["skills"]
    )
    asymmetric["assessments"][aid]["skills"][skill]["acceptable_evidence"].append(
        {"task": foreign_task, "minimum_score": 1}
    )
    try:
        validate_schema(asymmetric)
    except ValidationError as exc:
        require("ASSESS-EVIDENCE-BIDIRECTIONAL" in str(exc), f"ASSESS-SCHEMA-PROBE: wrong ownership diagnostic: {exc}")
    else:
        raise ValidationError("ASSESS-SCHEMA-PROBE: asymmetric evidence was accepted")

    # The proof domain must be derived from per-task maxima, not hard-coded to 0..2.
    expanded = copy.deepcopy(c)
    task = next(iter(expanded["assessments"][aid]["tasks"]))
    expanded["assessments"][aid]["tasks"][task]["maximum"] += 1
    expanded["assessments"][aid]["maximum"] += 1
    validate_schema(expanded)
    count = enumerate_checkpoint(expanded, aid)
    expected = math.prod(td["maximum"] + 1 for td in expanded["assessments"][aid]["tasks"].values())
    require(count == expected, f"ASSESS-DOMAIN-PROBE: visited {count}, expected {expected}")

    return {
        "duplicate_evidence": "REJECTED",
        "asymmetric_evidence": "REJECTED",
        "dynamic_domain_assignments": count,
    }


def main() -> int:
    try:
        contract = load_contract(ROOT)
        validate_schema(contract)
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
            "scripts/evidence_provenance.py",
            "tests/fixtures/scoring.json",
        ],
    )
    report = {
        "schema_version": "2.0",
        "source_digest": source_digest,
        "schema": "PASS",
        "schema_regression_probes": probes,
        "checkpoint_score_domains": {
            aid: {task: td["maximum"] for task, td in contract["assessments"][aid]["tasks"].items()}
            for aid in [f"CP{i}" for i in range(1, 7)]
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
