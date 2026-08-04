from __future__ import annotations

from typing import Any

REQUIRED_ASSESSMENTS = ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6", "FINAL"]
PARTIAL_CONDITION = "0 < score < task.maximum"

class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def outcome_key(assessment_id: str, skill: str) -> str:
    return skill if assessment_id != "FINAL" else f"final.{skill}"


def validate_schema(contract: dict[str, Any]) -> None:
    require(contract.get("schema_version") == "2.0", "ASSESS-SCHEMA: schema_version must be 2.0")
    require(
        contract.get("canonical_owner") == "scripts/assessment_contract.json",
        "ASSESS-OWNER: canonical owner changed",
    )
    require(
        contract["course_readiness"]["required_assessments"] == REQUIRED_ASSESSMENTS,
        "ASSESS-READINESS: readiness must compose CP1..CP6 + FINAL",
    )
    require(
        contract["day10"]["mandatory_sessions"] == ["10A", "10B", "10C", "10D", "10E"],
        "ASSESS-DAY10: mandatory core must be 10A..10E",
    )
    require(
        contract["day10"]["optional_sessions"] == ["10F"],
        "ASSESS-DAY10-BONUS: 10F must remain optional",
    )
    require(
        set(contract["day10"]["bonus_only"]) == {"10F", "01-16"},
        "ASSESS-BONUS: 10F and 01-16 must be bonus-only",
    )

    final_bonus = contract["assessments"]["FINAL"]["bonus_rules"]
    require(
        final_bonus.get("included_in_maximum") is False,
        "ASSESS-BONUS: bonus tasks must not be included in the final maximum",
    )
    require(
        final_bonus.get("bonus_can_compensate_mandatory") is False,
        "ASSESS-BONUS: bonus must not compensate mandatory evidence",
    )

    declared = contract.get("declared_outcomes")
    require(isinstance(declared, dict) and declared, "ASSESS-OUTCOME-COVERAGE: declared_outcomes missing")

    actual_owners: dict[str, str] = {}
    for assessment_id, assessment in contract["assessments"].items():
        require(assessment_id in REQUIRED_ASSESSMENTS, f"ASSESS-ID: unexpected assessment {assessment_id}")
        tasks = assessment["tasks"]
        require(tasks, f"ASSESS-TASKS {assessment_id}: assessment has no tasks")

        for task, task_data in tasks.items():
            maximum = task_data.get("maximum")
            require(
                isinstance(maximum, int) and not isinstance(maximum, bool) and maximum >= 1,
                f"ASSESS-TASK-MAXIMUM {assessment_id}/{task}: maximum must be a positive integer",
            )

        maximum = assessment.get("maximum")
        require(
            isinstance(maximum, int) and not isinstance(maximum, bool),
            f"ASSESS-MAXIMUM {assessment_id}: maximum must be an integer",
        )
        require(
            sum(task_data["maximum"] for task_data in tasks.values()) == maximum,
            f"ASSESS-MAXIMUM {assessment_id}: task maxima do not sum to assessment maximum",
        )
        threshold = assessment.get("threshold")
        require(
            isinstance(threshold, int)
            and not isinstance(threshold, bool)
            and 0 < threshold <= maximum,
            f"ASSESS-THRESHOLD {assessment_id}: invalid threshold",
        )

        if assessment["kind"] == "checkpoint":
            task_domain = sorted({score for task_data in tasks.values() for score in range(task_data["maximum"] + 1)})
            require(
                assessment.get("score_domain") == task_domain,
                f"ASSESS-SCORE-DOMAIN {assessment_id}: score_domain must equal {task_domain}",
            )
            partial_rule = assessment.get("partial_error_rule")
            dynamic_rule = {"condition": PARTIAL_CONDITION, "requires_new_variant": True}
            legacy_binary_rule = {"score": 1, "requires_new_variant": True}
            if all(task_data["maximum"] == 2 for task_data in tasks.values()):
                require(
                    partial_rule in (legacy_binary_rule, dynamic_rule),
                    f"ASSESS-PARTIAL-RULE {assessment_id}: runtime partial-score rule drifted",
                )
            else:
                require(
                    partial_rule == dynamic_rule,
                    f"ASSESS-PARTIAL-RULE {assessment_id}: non-binary task maxima require the dynamic rule",
                )
        else:
            require(
                assessment.get("score_domain") == "integer_0_to_task_maximum",
                "ASSESS-SCORE-DOMAIN FINAL: expected integer_0_to_task_maximum",
            )
            require(
                assessment.get("partial_error_rule")
                == {
                    "condition": PARTIAL_CONDITION,
                    "requires_new_variant_for_full_readiness": True,
                },
                "ASSESS-PARTIAL-RULE FINAL: runtime readiness rule drifted",
            )

        reverse_blocks: dict[str, set[str]] = {task: set() for task in tasks}
        for block, block_data in assessment["block_minimums"].items():
            block_tasks = block_data["tasks"]
            require(
                len(block_tasks) == len(set(block_tasks)),
                f"ASSESS-BLOCK-DUPLICATE {assessment_id}/{block}: duplicate task",
            )
            require(
                set(block_tasks) <= set(tasks),
                f"ASSESS-BLOCK {assessment_id}/{block}: unknown task",
            )
            minimum = block_data["minimum"]
            require(
                isinstance(minimum, int)
                and not isinstance(minimum, bool)
                and 0 <= minimum <= sum(tasks[task]["maximum"] for task in block_tasks),
                f"ASSESS-BLOCK {assessment_id}/{block}: impossible minimum",
            )
            for task in block_tasks:
                reverse_blocks[task].add(block)

        for task, task_data in tasks.items():
            memberships = task_data.get("block_membership")
            require(
                isinstance(memberships, list) and len(memberships) == len(set(memberships)),
                f"ASSESS-BLOCK-MEMBERSHIP {assessment_id}/{task}: invalid membership list",
            )
            require(
                set(memberships) == reverse_blocks[task],
                f"ASSESS-BLOCK-MEMBERSHIP {assessment_id}/{task}: {memberships} != {sorted(reverse_blocks[task])}",
            )

        critical_seen: set[str] = set()
        for rule in assessment["critical_task_rules"]:
            task = rule["task"]
            require(task in tasks, f"ASSESS-CRITICAL {assessment_id}: unknown task {task}")
            require(task not in critical_seen, f"ASSESS-CRITICAL-DUPLICATE {assessment_id}: {task}")
            critical_seen.add(task)
            minimum = rule["minimum_score"]
            require(
                isinstance(minimum, int)
                and not isinstance(minimum, bool)
                and 1 <= minimum <= tasks[task]["maximum"],
                f"ASSESS-CRITICAL {assessment_id}/{task}: invalid minimum",
            )

        for skill, skill_data in assessment["skills"].items():
            key = outcome_key(assessment_id, skill)
            require(key not in actual_owners, f"ASSESS-OUTCOME-DUPLICATE {key}: multiple owners")
            actual_owners[key] = assessment_id

            require(skill_data.get("mandatory") is True, f"ASSESS-MANDATORY {assessment_id}/{skill}: outcome is no longer mandatory")
            evidence = skill_data.get("acceptable_evidence")
            require(evidence, f"ASSESS-EVIDENCE {assessment_id}/{skill}: no acceptable evidence")

            seen_evidence: set[tuple[str, int]] = set()
            for evidence_rule in evidence:
                task = evidence_rule["task"]
                minimum = evidence_rule["minimum_score"]
                require(task in tasks, f"ASSESS-EVIDENCE {assessment_id}/{skill}: unknown task {task}")
                require(
                    isinstance(minimum, int)
                    and not isinstance(minimum, bool)
                    and 1 <= minimum <= tasks[task]["maximum"],
                    f"ASSESS-EVIDENCE {assessment_id}/{skill}: invalid minimum",
                )
                signature = (task, minimum)
                require(
                    signature not in seen_evidence,
                    f"ASSESS-EVIDENCE-DUPLICATE {assessment_id}/{skill}: duplicate {task}@{minimum}",
                )
                seen_evidence.add(signature)
                require(
                    skill in tasks[task].get("skills", []),
                    f"ASSESS-EVIDENCE-BIDIRECTIONAL {assessment_id}/{skill}: {task} accepts the skill but task.skills does not declare it",
                )

            minimum_evidence = skill_data.get("minimum_evidence")
            require(
                isinstance(minimum_evidence, int)
                and not isinstance(minimum_evidence, bool)
                and 1 <= minimum_evidence <= len(seen_evidence),
                f"ASSESS-EVIDENCE-MINIMUM {assessment_id}/{skill}: minimum_evidence is invalid",
            )

        for task, task_data in tasks.items():
            mapped = task_data.get("skills")
            require(mapped, f"ASSESS-TASK-SKILL {assessment_id}/{task}: task has no atomic skill mapping")
            require(
                len(mapped) == len(set(mapped)),
                f"ASSESS-TASK-SKILL-DUPLICATE {assessment_id}/{task}: duplicate skill mapping",
            )
            for skill in mapped:
                require(
                    skill in assessment["skills"],
                    f"ASSESS-TASK-SKILL {assessment_id}/{task}: unknown skill {skill}",
                )
                evidence_tasks = {
                    evidence_rule["task"]
                    for evidence_rule in assessment["skills"][skill]["acceptable_evidence"]
                }
                require(
                    task in evidence_tasks,
                    f"ASSESS-EVIDENCE-BIDIRECTIONAL {assessment_id}/{task}: mapped skill {skill} does not accept evidence from this task",
                )

    declared_keys = set(declared)
    actual_keys = set(actual_owners)
    require(
        declared_keys == actual_keys,
        "ASSESS-OUTCOME-COVERAGE: "
        f"orphan_declared={sorted(declared_keys - actual_keys)} "
        f"undeclared_actual={sorted(actual_keys - declared_keys)}",
    )
    for key, actual_owner in actual_owners.items():
        outcome_data = declared[key]
        require(
            outcome_data.get("mandatory") is True,
            f"ASSESS-OUTCOME-MANDATORY {key}: declared outcome must remain mandatory",
        )
        require(
            outcome_data.get("owner_assessment") == actual_owner,
            f"ASSESS-OUTCOME-OWNER {key}: {outcome_data.get('owner_assessment')} != {actual_owner}",
        )
