from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY=sys.executable

MUTATIONS=[
 ('M01-cleanup-16-to-8','examples/14_scanf_call.asm','add esp, 16','add esp, 8','semantics','ASM-CALL-AREA'),
 ('M02-remove-padding','examples/14_scanf_call.asm','    sub esp, 8\n','','semantics','ASM-CALL-AREA'),
 ('M03-remove-cdq','examples/11_idiv_overflow_negative.asm','    cdq\n','','semantics','ASM-IDIV-CDQ'),
 ('M04-reverse-fsubp','examples/13_x87_order.asm','fsubp st1, st0','fsubrp st1, st0','semantics','ASM-X87-SUB'),
 ('M05-reverse-fdivp','examples/13_x87_order.asm','fdivp st1, st0','fdivrp st1, st0','semantics','ASM-X87-DIV'),
 ('M06-remove-restore-esi','examples/12_callee_saved.asm','    pop esi\n','','semantics','ASM-CALLEE-SAVED'),
 ('M07-scanf-value','examples/14_scanf_call.asm','    push x\n','    push dword [x]\n','semantics','ASM-SCANF-ADDRESS'),
 ('M08-idiv-immediate','examples/11_idiv_overflow_negative.asm','    idiv ecx\n','    idiv -1\n','semantics','ASM-IDIV-OPERAND'),
 ('M09-make-10F-core','scripts/assessment_contract.json','"optional_sessions": [\n      "10F"\n    ]','"optional_sessions": []','assessment','ASSESS-DAY10-BONUS'),
 ('M10-include-01-16-in-100','scripts/assessment_contract.json','"included_in_maximum": false','"included_in_maximum": true','assessment','ASSESS-BONUS'),
 ('M11-remove-cp3-loop-evidence','scripts/assessment_contract.json','"mandatory": true,\n          "minimum_evidence": 1,\n          "acceptable_evidence": [\n            {\n              "task": "CP3-LOOP"','"mandatory": true,\n          "minimum_evidence": 1,\n          "acceptable_evidence": [\n            {\n              "task": "CP3-TABLE"','assessment','ASSESS-TASK-SKILL'),
 ('M12-safety-optional','scripts/assessment_contract.json','"memory_safety_boundaries": {\n          "mandatory": true','"memory_safety_boundaries": {\n          "mandatory": false','assessment','ASSESS-MANDATORY'),
 ('M13-remove-refreshers-manifest','scripts/course_manifest.py','    "docs/prerequisite_refreshers.md",\n','','semantics','MANIFEST-STANDALONE'),
 ('M14-answer-in-closed-book','docs/closed_book_workbook.md','# Тетрадь NASM IA-32 без встроенных ответов','# Тетрадь NASM IA-32 без встроенных ответов\n\n## Ответ\nsub esp, 8\npush dword [b]\npush dword [a]\ncall sum\nadd esp, 16','semantics','LEAK-C3'),
 ('M15-transfer-without-key','docs/transfer_workbook.md','`Container* c`','`Holder* c`','semantics','TRANSFER-SYNC'),
 ('M16-change-cp-threshold','scripts/assessment_contract.json','"maximum": 100,\n      "threshold": 80','"maximum": 100,\n      "threshold": 81','semantics','DOCS-ASSESSMENT'),
 ('M17-break-anchor','docs/day_10_learning_path.md','<a id="10b-safe-ceil-machine-model"></a>','<a id="renamed"></a>','semantics','LINK-ANCHOR'),
 ('M18-reverse-startup','docs/instruction_reference.md','exec → loader → _start → runtime startup → main → exit','main → runtime startup → _start → loader → exec','semantics','STARTUP-DIRECTION'),
 ('M19-return-c3-to-day25','docs/day_25.md','\n## Порядок после попытки','\n```asm\nsub esp, 8\npush dword [b]\npush dword [a]\ncall sum\nadd esp, 16\n```\n\n## Порядок после попытки','semantics','LEAK-C3'),
 ('M20-accept-known-false-pass','tests/fixtures/scoring.json','"expected_pass": false','"expected_pass": true','assessment','ASSESS-REGRESSION'),
]

def run_owner(root: Path, owner: str) -> subprocess.CompletedProcess[str]:
    script='validate_assessment.py' if owner=='assessment' else 'validate_semantics.py'
    return subprocess.run([PY,str(root/'scripts'/script)],cwd=root,text=True,capture_output=True)

def main()->int:
    rows=[]
    for mid,rel,old,new,owner,expected in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix='nasm-mutation-') as td:
            dst=Path(td)/'repo'
            shutil.copytree(ROOT,dst,ignore=shutil.ignore_patterns('node_modules','.git','MUTATION_REPORT.*','ASSESSMENT_PROOF.json','render-evidence'))
            p=dst/rel
            text=p.read_text(encoding='utf-8')
            if old not in text:
                rows.append({'id':mid,'owner':owner,'expected':expected,'exit_code':99,'message':'mutation source fragment not found','pass':False})
                continue
            p.write_text(text.replace(old,new,1),encoding='utf-8')
            cp=run_owner(dst,owner)
            out=(cp.stdout+'\n'+cp.stderr).strip()
            ok=cp.returncode!=0 and expected in out
            rows.append({'id':mid,'owner':owner,'expected':expected,'exit_code':cp.returncode,'message':out[-1000:],'pass':ok})
    (ROOT/'MUTATION_REPORT.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Mutation report','','| ID | Owner | Expected diagnostic | Exit | Result |','|---|---|---|---:|---|']
    for r in rows: lines.append(f'| {r["id"]} | {r["owner"]} | `{r["expected"]}` | {r["exit_code"]} | {"PASS" if r["pass"] else "FAIL"} |')
    lines += ['','## Diagnostics']
    for r in rows: lines += ['',f'### {r["id"]}','```text',r['message'],'```']
    (ROOT/'MUTATION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    failed=[r for r in rows if not r['pass']]
    print(f'MUTATIONS_TOTAL={len(rows)}')
    print(f'MUTATIONS_CAUGHT={len(rows)-len(failed)}')
    if failed:
        for r in failed: print(f'MUTATION_FAIL {r["id"]}: {r["message"]}',file=sys.stderr)
        return 1
    print('MUTATION_SUITE=PASS')
    return 0
if __name__=='__main__': raise SystemExit(main())
