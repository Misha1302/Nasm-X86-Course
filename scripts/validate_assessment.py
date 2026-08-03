from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

from assessment_engine import evaluate, load_contract
from verification_provenance import provenance

ROOT = Path(__file__).resolve().parents[1]

class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_schema(c: dict[str, Any]) -> None:
    require(c.get('schema_version') == '2.0', 'ASSESS-SCHEMA: schema_version must be 2.0')
    require(c.get('canonical_owner') == 'scripts/assessment_contract.json', 'ASSESS-OWNER: canonical owner changed')
    required = ['CP1','CP2','CP3','CP4','CP5','CP6','FINAL']
    require(c['course_readiness']['required_assessments'] == required, 'ASSESS-READINESS: readiness must compose CP1..CP6 + FINAL')
    require(c['day10']['mandatory_sessions'] == ['10A','10B','10C','10D','10E'], 'ASSESS-DAY10: mandatory core must be 10A..10E')
    require(c['day10']['optional_sessions'] == ['10F'], 'ASSESS-DAY10-BONUS: 10F must remain optional')
    require(set(c['day10']['bonus_only']) == {'10F','01-16'}, 'ASSESS-BONUS: 10F and 01-16 must be bonus-only')
    fb = c['assessments']['FINAL']['bonus_rules']
    require(fb.get('included_in_maximum') is False, 'ASSESS-BONUS: bonus tasks must not be included in the final maximum')
    require(fb.get('bonus_can_compensate_mandatory') is False, 'ASSESS-BONUS: bonus must not compensate mandatory evidence')

    outcome_owner = c['declared_outcomes']
    for aid, a in c['assessments'].items():
        require(sum(t['maximum'] for t in a['tasks'].values()) == a['maximum'], f'ASSESS-MAXIMUM {aid}: task maxima do not sum to assessment maximum')
        require(0 < a['threshold'] <= a['maximum'], f'ASSESS-THRESHOLD {aid}: invalid threshold')
        for block, bd in a['block_minimums'].items():
            require(set(bd['tasks']) <= set(a['tasks']), f'ASSESS-BLOCK {aid}/{block}: unknown task')
            require(0 <= bd['minimum'] <= sum(a['tasks'][t]['maximum'] for t in bd['tasks']), f'ASSESS-BLOCK {aid}/{block}: impossible minimum')
        evidence_by_skill: dict[str, set[str]] = {}
        for skill, sd in a['skills'].items():
            key = skill if aid != 'FINAL' else 'final.' + skill
            require(key in outcome_owner and outcome_owner[key]['mandatory'], f'ASSESS-OUTCOME {aid}/{skill}: mandatory outcome disappeared')
            require(sd.get('mandatory') is True, f'ASSESS-MANDATORY {aid}/{skill}: outcome is no longer mandatory')
            evidence = sd.get('acceptable_evidence')
            require(evidence, f'ASSESS-EVIDENCE {aid}/{skill}: no acceptable evidence')
            tasks_seen: set[str] = set()
            records_seen: set[tuple[str, int]] = set()
            for ev in evidence:
                record = (ev['task'], ev['minimum_score'])
                require(record not in records_seen, f'ASSESS-EVIDENCE-DUP {aid}/{skill}: duplicate evidence {record}')
                require(ev['task'] not in tasks_seen, f'ASSESS-EVIDENCE-DUP {aid}/{skill}: one task counted more than once')
                records_seen.add(record); tasks_seen.add(ev['task'])
                require(ev['task'] in a['tasks'], f'ASSESS-EVIDENCE {aid}/{skill}: unknown task {ev["task"]}')
                require(1 <= ev['minimum_score'] <= a['tasks'][ev['task']]['maximum'], f'ASSESS-EVIDENCE {aid}/{skill}: invalid minimum')
            require(1 <= sd['minimum_evidence'] <= len(tasks_seen), f'ASSESS-EVIDENCE {aid}/{skill}: impossible minimum_evidence')
            evidence_by_skill[skill] = tasks_seen
        mapped_by_skill = {skill: set() for skill in a['skills']}
        for task, td in a['tasks'].items():
            require(td.get('skills'), f'ASSESS-TASK-SKILL {aid}/{task}: task has no atomic skill mapping')
            require(len(td['skills']) == len(set(td['skills'])), f'ASSESS-TASK-SKILL {aid}/{task}: duplicate skill mapping')
            for skill in td['skills']:
                require(skill in a['skills'], f'ASSESS-TASK-SKILL {aid}/{task}: unknown skill {skill}')
                mapped_by_skill[skill].add(task)
        for skill in a['skills']:
            require(mapped_by_skill[skill] == evidence_by_skill[skill], f'ASSESS-EVIDENCE-BIDIRECTIONAL {aid}/{skill}: task.skills={sorted(mapped_by_skill[skill])} evidence={sorted(evidence_by_skill[skill])}')


def exhaustive_checkpoint(c: dict[str, Any], aid: str) -> int:
    tasks = list(c['assessments'][aid]['tasks'])
    ranges = [range(c['assessments'][aid]['tasks'][task]['maximum'] + 1) for task in tasks]
    visited = 0
    for values in itertools.product(*ranges):
        visited += 1
        scores = dict(zip(tasks, values))
        variants = {t for t,v in scores.items() if 0 < v < c['assessments'][aid]['tasks'][t]['maximum']}
        d = evaluate(aid, scores, new_variants=variants, contract=c)
        if d.passed:
            for skill, sd in c['assessments'][aid]['skills'].items():
                evidence = sum(scores[e['task']] >= e['minimum_score'] for e in sd['acceptable_evidence'])
                require(evidence >= sd['minimum_evidence'], f'ASSESS-FALSE-PASS {aid}: {skill} missing for {scores}')
    expected = math.prod(c['assessments'][aid]['tasks'][task]['maximum'] + 1 for task in tasks)
    require(visited == expected, f'ASSESS-EXHAUSTIVE-DOMAIN {aid}: visited {visited}, expected {expected}')
    return visited


def exhaustive_checkpoints(c: dict[str, Any]) -> dict[str, int]:
    return {aid: exhaustive_checkpoint(c, aid) for aid in [f'CP{i}' for i in range(1,7)]}


def monotone_final_constraint_proof(c: dict[str, Any]) -> dict[str, Any]:
    a = c['assessments']['FINAL']
    checked = 0
    witnesses: list[dict[str, Any]] = []
    for skill, sd in a['skills'].items():
        evidence_tasks = sorted({ev['task'] for ev in sd['acceptable_evidence']})
        ranges = [range(a['tasks'][t]['maximum'] + 1) for t in evidence_tasks]
        for vals in itertools.product(*ranges):
            scores = {t: td['maximum'] for t,td in a['tasks'].items()}
            scores.update(dict(zip(evidence_tasks, vals)))
            evidence = sum(scores[ev['task']] >= ev['minimum_score'] for ev in sd['acceptable_evidence'])
            if evidence >= sd['minimum_evidence']:
                continue
            checked += 1
            d = evaluate('FINAL', scores, new_variants=set(a['tasks']), contract=c, readiness=True)
            if d.passed:
                witnesses.append({'skill':skill,'scores':scores})
    require(not witnesses, f'ASSESS-FINAL-FALSE-PASS: {witnesses[:1]}')
    return {'solver':'monotone bounded constraint enumeration','assignments_checked':checked,'witnesses':witnesses}


def regression_fixtures(c: dict[str, Any]) -> dict[str, Any]:
    fixtures = json.loads((ROOT/'tests/fixtures/scoring.json').read_text(encoding='utf-8'))
    results = {}
    for f in fixtures:
        d = evaluate(f['assessment'], f['scores'], new_variants=set(f.get('new_variants', [])), contract=c, readiness=f.get('readiness',False))
        require(d.passed == f['expected_pass'], f'ASSESS-REGRESSION {f["id"]}: expected {f["expected_pass"]}, got {d.passed}; {d.failures}')
        if 'expected_missing_skill' in f:
            require(f['expected_missing_skill'] in d.missing_skills, f'ASSESS-REGRESSION {f["id"]}: expected missing skill {f["expected_missing_skill"]}; got {d.missing_skills}')
        results[f['id']] = d.to_dict()
    return results


def expect_schema_failure(c: dict[str, Any], marker: str) -> None:
    try:
        validate_schema(c)
    except ValidationError as exc:
        require(marker in str(exc), f'ASSESS-SELFTEST: expected {marker}, got {exc}')
    else:
        raise ValidationError(f'ASSESS-SELFTEST: malformed contract escaped {marker}')


def validator_selftests(c: dict[str, Any]) -> dict[str, Any]:
    dynamic = copy.deepcopy(c)
    aid='CP1'; task=next(iter(dynamic['assessments'][aid]['tasks']))
    dynamic['assessments'][aid]['tasks'][task]['maximum'] += 1
    dynamic['assessments'][aid]['maximum'] += 1
    validate_schema(dynamic)
    visited = exhaustive_checkpoint(dynamic, aid)
    expected = math.prod(td['maximum'] + 1 for td in dynamic['assessments'][aid]['tasks'].values())
    require(visited == expected, 'ASSESS-SELFTEST: dynamic score domain not exhaustive')

    duplicate = copy.deepcopy(c)
    aid='CP1'; skill=next(iter(duplicate['assessments'][aid]['skills']))
    duplicate['assessments'][aid]['skills'][skill]['acceptable_evidence'].append(copy.deepcopy(duplicate['assessments'][aid]['skills'][skill]['acceptable_evidence'][0]))
    expect_schema_failure(duplicate, 'ASSESS-EVIDENCE-DUP')

    asymmetric = copy.deepcopy(c)
    aid='CP1'; skill=next(iter(asymmetric['assessments'][aid]['skills']))
    existing={ev['task'] for ev in asymmetric['assessments'][aid]['skills'][skill]['acceptable_evidence']}
    extra=next(task for task in asymmetric['assessments'][aid]['tasks'] if task not in existing)
    asymmetric['assessments'][aid]['skills'][skill]['acceptable_evidence'].append({'task':extra,'minimum_score':1})
    expect_schema_failure(asymmetric, 'ASSESS-EVIDENCE-BIDIRECTIONAL')
    return {'dynamic_domain_assignments': visited, 'duplicate_evidence_rejected': True, 'asymmetric_mapping_rejected': True}


def main() -> int:
    try:
        c = load_contract(ROOT)
        validate_schema(c)
        selftests = validator_selftests(c)
        exhaustive = exhaustive_checkpoints(c)
        final_proof = monotone_final_constraint_proof(c)
        regressions = regression_fixtures(c)
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    report = {
        'schema_version':'2.0',
        'result':'PASS',
        'provenance':provenance(ROOT, Path(__file__).resolve()),
        'validator_selftests':selftests,
        'exhaustive_checkpoint_assignments':exhaustive,
        'final_constraint_proof':final_proof,
        'regressions':regressions,
    }
    (ROOT/'ASSESSMENT_PROOF.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ASSESSMENT_SCHEMA=PASS')
    print('ASSESSMENT_VALIDATOR_SELFTESTS=PASS')
    print('CHECKPOINT_EXHAUSTIVE=PASS ' + ' '.join(f'{k}:{v}' for k,v in exhaustive.items()))
    print(f'FINAL_CONSTRAINT_PROOF=PASS checked={final_proof["assignments_checked"]}')
    print(f'SCORING_REGRESSIONS=PASS count={len(regressions)}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
