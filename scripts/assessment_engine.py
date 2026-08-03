from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json

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
    return json.loads((root / 'scripts/assessment_contract.json').read_text(encoding='utf-8'))


def evaluate(assessment_id: str, scores: dict[str, int], *, new_variants: set[str] | None = None, contract: dict[str, Any] | None = None, readiness: bool = False) -> Decision:
    contract = contract or load_contract()
    a = contract['assessments'][assessment_id]
    new_variants = new_variants or set()
    failures: list[str] = []
    missing_skills: list[str] = []
    missing_variants: list[str] = []

    expected = set(a['tasks'])
    unknown = set(scores) - expected
    if unknown:
        failures.append('unknown tasks: ' + ', '.join(sorted(unknown)))
    for task, td in a['tasks'].items():
        score = scores.get(task, 0)
        maximum = td['maximum']
        if type(score) is not int or score < 0 or score > maximum:
            failures.append(f'{task}: score {score!r} outside 0..{maximum}')

    total = sum(scores.get(task, 0) for task in a['tasks'])
    if total < a['threshold']:
        failures.append(f'total {total} < threshold {a["threshold"]}')

    for block, bd in a['block_minimums'].items():
        got = sum(scores.get(task, 0) for task in bd['tasks'])
        if got < bd['minimum']:
            failures.append(f'block {block}: {got} < {bd["minimum"]}')

    for rule in a['critical_task_rules']:
        got = scores.get(rule['task'], 0)
        if got < rule['minimum_score']:
            failures.append(f'critical {rule["task"]}: {got} < {rule["minimum_score"]}')

    for skill, sd in a['skills'].items():
        if not sd.get('mandatory', False):
            continue
        evidence = sum(1 for ev in sd['acceptable_evidence'] if scores.get(ev['task'], 0) >= ev['minimum_score'])
        if evidence < sd['minimum_evidence']:
            missing_skills.append(skill)
            failures.append(f'mandatory skill {skill}: evidence {evidence} < {sd["minimum_evidence"]}')

    if a['kind'] == 'checkpoint':
        for task, td in a['tasks'].items():
            if scores.get(task, 0) == 1 and task not in new_variants:
                missing_variants.append(task)
                failures.append(f'{task}: partial score requires a new variant')
    elif readiness:
        for task, td in a['tasks'].items():
            score = scores.get(task, 0)
            if 0 < score < td['maximum'] and task not in new_variants:
                missing_variants.append(task)
                failures.append(f'{task}: partial final evidence requires a new variant for full readiness')

    return Decision(assessment_id, not failures, total, tuple(failures), tuple(missing_skills), tuple(missing_variants))


def evaluate_course(all_scores: dict[str, dict[str, int]], *, variants: dict[str, set[str]] | None = None, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    variants = variants or {}
    decisions = {
        aid: evaluate(aid, all_scores.get(aid, {}), new_variants=variants.get(aid, set()), contract=contract, readiness=True)
        for aid in contract['course_readiness']['required_assessments']
    }
    return {'ready': all(d.passed for d in decisions.values()), 'assessments': {k:v.to_dict() for k,v in decisions.items()}}
