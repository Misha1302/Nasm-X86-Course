from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from assessment_engine import evaluate, load_contract
from verification_provenance import file_sha256, provenance, verification_source_digest

ROOT = Path(__file__).resolve().parents[1]

def require(condition: bool, message: str) -> None:
    if not condition: raise RuntimeError(message)

def main() -> int:
    contract=load_contract(ROOT); attacks=[]
    for aid,assessment in contract['assessments'].items():
        for skill,sd in assessment['skills'].items():
            if not sd.get('mandatory'): continue
            scores={task:td['maximum'] for task,td in assessment['tasks'].items()}
            for evidence in sd['acceptable_evidence']: scores[evidence['task']]=max(0,evidence['minimum_score']-1)
            decision=evaluate(aid,scores,new_variants=set(assessment['tasks']),contract=contract,readiness=True)
            require(not decision.passed,f'ADVERSARIAL-FALSE-PASS {aid}/{skill}')
            require(skill in decision.missing_skills,f'ADVERSARIAL-WRONG-OWNER {aid}/{skill}: {decision.failures}')
            attacks.append({'assessment':aid,'skill':skill,'result':'BLOCKED','failures':list(decision.failures)})

    owners=[]
    for path in sorted((ROOT/'scripts').glob('*.json')):
        try: data=json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError: continue
        if isinstance(data,dict) and 'assessments' in data: owners.append(str(path.relative_to(ROOT)))
    require(owners==['scripts/assessment_contract.json'],f'ADVERSARIAL-COMPETING-OWNER: {owners}')

    semantic=subprocess.run([sys.executable,str(ROOT/'scripts/validate_semantics.py')],cwd=ROOT,text=True,capture_output=True)
    require(semantic.returncode==0,'ADVERSARIAL-SEMANTICS: '+semantic.stdout+semantic.stderr)

    for rel in ('MUTATION_REPORT.json','MUTATION_REPORT.md'):
        (ROOT/rel).unlink(missing_ok=True)
    mutation_run=subprocess.run([sys.executable,str(ROOT/'scripts/run_mutations.py')],cwd=ROOT,text=True,capture_output=True)
    require(mutation_run.returncode==0,'ADVERSARIAL-MUTATION-RUN: '+mutation_run.stdout+mutation_run.stderr)
    mutation_path=ROOT/'MUTATION_REPORT.json'
    require(mutation_path.is_file(),'ADVERSARIAL-MUTATION-FRESHNESS: fresh report missing')
    mutation=json.loads(mutation_path.read_text(encoding='utf-8'))
    mutation_contract=json.loads((ROOT/'scripts/mutation_contract.json').read_text(encoding='utf-8'))
    expected_ids=[item['id'] for item in mutation_contract['mutations']]
    require(mutation.get('mutation_ids')==expected_ids,'ADVERSARIAL-MUTATION-IDS: report does not match current suite')
    require(mutation.get('provenance',{}).get('source_tree_sha256')==verification_source_digest(ROOT),'ADVERSARIAL-MUTATION-FRESHNESS: source digest mismatch')
    require(mutation.get('provenance',{}).get('runner_sha256')==file_sha256(ROOT/'scripts/run_mutations.py'),'ADVERSARIAL-MUTATION-FRESHNESS: runner digest mismatch')
    results=mutation.get('results',[])
    require(len(results)==len(expected_ids) and all(row.get('pass') is True for row in results),'ADVERSARIAL-MUTATIONS: incomplete mutation coverage')

    report={'schema_version':'2.0','result':'PASS','provenance':provenance(ROOT,Path(__file__).resolve()),'mandatory_skill_attacks':attacks,'mandatory_skill_attack_count':len(attacks),'competing_assessment_owners':owners,'mutation_report_sha256':file_sha256(mutation_path),'mutation_evasion_attempts':len(results),'mutation_evasion_survivors':0,'day25_and_closed_book_leakage':'BLOCKED_BY_VISIBLE_TEXT_VALIDATION','day10_future_dependency':'BLOCKED_BY_ACTUAL_SOURCE_ORDER','transfer_copy_attacks':'BLOCKED_BY_TRANSFER_FINGERPRINTS_AND_STRUCTURE'}
    (ROOT/'ADVERSARIAL_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md=['# Adversarial review','',f'- Source tree: `{report["provenance"]["source_tree_sha256"]}`.',f'- Mandatory-skill false-PASS attacks: **{len(attacks)} blocked**.','- Rendered-text answer leakage: **blocked**.','- Actual-source pedagogy ordering: **verified**.',f'- Mutation evasions: **{len(results)} attempted, 0 survived**.','- Competing machine-readable assessment owner: **none**.','','Result: **PASS**.']
    (ROOT/'ADVERSARIAL_REVIEW.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(f'ADVERSARIAL_MANDATORY_SKILL_ATTACKS={len(attacks)}'); print('ADVERSARIAL_MUTATION_SURVIVORS=0'); print('ADVERSARIAL_COMPETING_OWNER=NONE'); print('ADVERSARIAL_REVIEW=PASS'); return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except RuntimeError as exc: print(str(exc),file=sys.stderr); raise SystemExit(1)
