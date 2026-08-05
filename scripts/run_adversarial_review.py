from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from assessment_engine import evaluate, load_contract
from evidence_provenance import digest_paths

ROOT = Path(__file__).resolve().parents[1]


class AdversarialError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdversarialError(message)


def load_mutation_contract() -> dict[str, Any]:
    data = json.loads((ROOT / "scripts" / "mutation_contract.json").read_text(encoding="utf-8"))
    require(data.get("schema_version") == "3.0", "ADVERSARIAL-MUTATION-CONTRACT: invalid schema")
    require(isinstance(data.get("cases"), list), "ADVERSARIAL-MUTATION-CONTRACT: cases missing")
    return data


def mutation_source_digest(contract: dict[str, Any]) -> str:
    paths = [case["path"] for case in contract["cases"]]
    paths += [
        "scripts/mutation_contract.json",
        "scripts/run_mutations.py",
        "scripts/verify_mutation_execution.py",
        "scripts/validate_semantics.py",
        "scripts/validate_assessment.py",
        "scripts/assessment_schema.py",
        "scripts/assessment_engine.py",
        "scripts/content_normalization.py",
        "scripts/evidence_provenance.py",
    ]
    return digest_paths(ROOT, paths)


def run_reporting_mutations() -> dict[str, Any]:
    contract = load_mutation_contract()
    for relative in ("MUTATION_REPORT.json", "MUTATION_REPORT.md"):
        path = ROOT / relative
        if path.exists():
            path.unlink()

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_mutations.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    output = result.stdout + result.stderr
    require(result.returncode == 0, "ADVERSARIAL-MUTATION-RUN: " + output[-5000:])
    require(
        f"MUTATIONS_TOTAL={len(contract['cases'])}" in output and "MUTATION_SUITE=PASS" in output,
        "ADVERSARIAL-MUTATION-RECEIPT: reporting runner did not emit exact completion receipt",
    )

    path = ROOT / "MUTATION_REPORT.json"
    require(path.is_file(), "ADVERSARIAL-MUTATION-REPORT: missing fresh report")
    report = json.loads(path.read_text(encoding="utf-8"))
    require(report.get("schema_version") == "3.0", "ADVERSARIAL-MUTATION-REPORT: invalid schema")
    expected_digest = mutation_source_digest(contract)
    require(
        report.get("source_digest") == expected_digest,
        f"ADVERSARIAL-MUTATION-FRESHNESS: {report.get('source_digest')} != {expected_digest}",
    )
    rows = report.get("cases")
    require(isinstance(rows, list), "ADVERSARIAL-MUTATION-REPORT: cases missing")
    expected_ids = [case["id"] for case in contract["cases"]]
    actual_ids = [row.get("id") for row in rows]
    require(actual_ids == expected_ids, f"ADVERSARIAL-MUTATION-IDS: {actual_ids} != {expected_ids}")
    require(all(row.get("pass") is True for row in rows), "ADVERSARIAL-MUTATIONS: reporting runner recorded survivor")
    return report


def run_independent_oracle(expected_cases: int) -> dict[str, Any]:
    oracle_path = ROOT / "MUTATION_ORACLE.json"
    if oracle_path.exists():
        oracle_path.unlink()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_mutation_execution.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    output = result.stdout + result.stderr
    require(result.returncode == 0, "ADVERSARIAL-MUTATION-ORACLE: " + output[-5000:])
    require(
        f"MUTATION_ORACLE_CASES={expected_cases}" in output
        and "MUTATION_ORACLE_RESULT=PASS" in output,
        "ADVERSARIAL-MUTATION-ORACLE-RECEIPT: independent oracle receipt missing",
    )
    require(oracle_path.is_file(), "ADVERSARIAL-MUTATION-ORACLE-REPORT: missing report")
    report = json.loads(oracle_path.read_text(encoding="utf-8"))
    require(report.get("result") == "PASS", "ADVERSARIAL-MUTATION-ORACLE-REPORT: result is not PASS")
    rows = report.get("cases")
    require(isinstance(rows, list) and len(rows) == expected_cases, "ADVERSARIAL-MUTATION-ORACLE-REPORT: incomplete cases")
    require(all(row.get("result") == "BLOCKED" for row in rows), "ADVERSARIAL-MUTATION-ORACLE-REPORT: survivor recorded")
    return report


def main() -> int:
    contract = load_contract(ROOT)
    attacks: list[dict[str, Any]] = []
    for assessment_id, assessment in contract["assessments"].items():
        for skill, skill_data in assessment["skills"].items():
            if not skill_data.get("mandatory"):
                continue
            scores = {task: task_data["maximum"] for task, task_data in assessment["tasks"].items()}
            for evidence in skill_data["acceptable_evidence"]:
                scores[evidence["task"]] = max(0, evidence["minimum_score"] - 1)
            decision = evaluate(
                assessment_id,
                scores,
                new_variants=set(assessment["tasks"]),
                contract=contract,
                readiness=True,
            )
            require(not decision.passed, f"ADVERSARIAL-FALSE-PASS {assessment_id}/{skill}")
            require(
                skill in decision.missing_skills,
                f"ADVERSARIAL-WRONG-OWNER {assessment_id}/{skill}: {decision.failures}",
            )
            attacks.append(
                {
                    "assessment": assessment_id,
                    "skill": skill,
                    "result": "BLOCKED",
                    "failures": list(decision.failures),
                }
            )

    machine_owners: list[str] = []
    for path in sorted((ROOT / "scripts").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "assessments" in data:
            machine_owners.append(str(path.relative_to(ROOT)))
    require(
        machine_owners == ["scripts/assessment_contract.json"],
        f"ADVERSARIAL-COMPETING-OWNER: {machine_owners}",
    )

    semantic = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_semantics.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    require(semantic.returncode == 0, "ADVERSARIAL-SEMANTICS: " + semantic.stdout + semantic.stderr)

    mutation_contract = load_mutation_contract()
    print("ADVERSARIAL_STAGE=REPORTING_MUTATIONS", flush=True)
    runner_report = run_reporting_mutations()
    print("ADVERSARIAL_STAGE=INDEPENDENT_ORACLE", flush=True)
    oracle_report = run_independent_oracle(len(mutation_contract["cases"]))
    print("ADVERSARIAL_STAGE=REPORT", flush=True)

    source_digest = digest_paths(
        ROOT,
        [
            "scripts/run_adversarial_review.py",
            "scripts/assessment_contract.json",
            "scripts/assessment_engine.py",
            "scripts/validate_semantics.py",
            "scripts/validate_assessment.py",
            "scripts/assessment_schema.py",
            "scripts/mutation_contract.json",
            "scripts/run_mutations.py",
            "scripts/verify_mutation_execution.py",
            "scripts/content_normalization.py",
        ],
    )
    report = {
        "schema_version": "3.0",
        "source_digest": source_digest,
        "mandatory_skill_attacks": attacks,
        "mandatory_skill_attack_count": len(attacks),
        "competing_assessment_owners": machine_owners,
        "day25_and_closed_book_leakage": "BLOCKED_BY_RENDERED_TEXT_NORMALIZATION",
        "day10_future_dependency": "BLOCKED_BY_ACTUAL_SOURCE_POSITION_AND_SECTION_CONTENT",
        "transfer_copy_attacks": "BLOCKED_BY_STRUCTURE_SYNC_FINGERPRINTS_AND_COUNTEREXAMPLES",
        "mutation_reporting_source_digest": runner_report["source_digest"],
        "mutation_policy_sha256": oracle_report["policy_sha256"],
        "mutation_evasion_attempts": len(oracle_report["cases"]),
        "mutation_evasion_survivors": 0,
        "mutation_authority": "INDEPENDENT_ORACLE",
        "result": "PASS",
    }
    (ROOT / "ADVERSARIAL_REVIEW.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown = [
        "# Adversarial review",
        "",
        f"- Source digest: `{source_digest}`",
        f"- Mandatory-skill false-PASS attacks: **{len(attacks)} blocked**.",
        "- Answer leakage on `day_25` and closed-book, including HTML-comment obfuscation: **blocked**.",
        "- Day 10 explanation/use/assessment order: **checked from actual source positions and exact section content**.",
        "- Transfer copy/rename attacks: **blocked by structure, sync fingerprints and diagnostic counterexamples**.",
        f"- Mutation cases: **{len(oracle_report['cases'])} independently re-executed, 0 survived**.",
        "- Reporting runner is non-authoritative; the independent oracle owns the merge decision.",
        "- Competing machine-readable assessment owner: **none**.",
        "",
        "Result: **PASS**.",
    ]
    (ROOT / "ADVERSARIAL_REVIEW.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"ADVERSARIAL_SOURCE_DIGEST={source_digest}")
    print(f"ADVERSARIAL_MANDATORY_SKILL_ATTACKS={len(attacks)}")
    print(f"ADVERSARIAL_MUTATION_CASES={len(oracle_report['cases'])}")
    print("ADVERSARIAL_MUTATION_ORACLE=PASS")
    print("ADVERSARIAL_MUTATION_SURVIVORS=0")
    print("ADVERSARIAL_COMPETING_OWNER=NONE")
    print("ADVERSARIAL_REVIEW=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AdversarialError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
