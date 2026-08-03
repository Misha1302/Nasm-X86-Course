from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

class VError(RuntimeError): pass

def require(c: bool, msg: str) -> None:
    if not c: raise VError(msg)

def strip_comments(s: str) -> str:
    return '\n'.join(line.split(';',1)[0] for line in s.splitlines())

def _normalize(s: str) -> str:
    s = s.lower()
    s = s.replace('dword ptr','dword').replace('byte ptr','byte').replace('word ptr','word')
    return re.sub(r'[^a-z0-9_+%\[\]=<>!*/-]+','',s)

def norm(s: str) -> str:
    return _normalize(strip_comments(s))

def norm_fingerprint(s: str) -> str:
    # Contract fingerprints use semicolons as instruction separators, not comments.
    return _normalize(s)

def section(text: str, anchor: str, next_anchor: str | None = None) -> str:
    start = text.index(f'<a id="{anchor}"></a>')
    if next_anchor:
        end = text.index(f'<a id="{next_anchor}"></a>', start)
    else:
        match = re.search(r'(?m)^<a id="[^"]+"></a>\s*$', text[start + 1:])
        end = start + 1 + match.start() if match else len(text)
    return text[start:end]

def exact_anchor_section(text: str, anchor: str) -> str:
    start = text.index(f'<a id="{anchor}"></a>')
    match = re.search(r'(?m)^<a id="[^"]+"></a>\s*$', text[start + 1:])
    end = start + 1 + match.start() if match else len(text)
    return text[start:end]

def validate_leakage() -> None:
    c=json.loads((ROOT/'scripts/answer_fingerprints.json').read_text(encoding='utf-8'))
    for rel in c['protected_targets']:
        text=(ROOT/rel).read_text(encoding='utf-8')
        nt=norm(text)
        for fp in c['fingerprints']:
            if rel not in fp.get('protected_targets', c['protected_targets']):
                continue
            nf=norm_fingerprint(fp['fragment'])
            if nf and nf in nt:
                raise VError(f'LEAK-{fp["task"]}: {rel} contains protected fingerprint {fp["id"]}: {fp["fragment"][:80]}')
        if rel.endswith('closed_book_workbook.md'):
            low=text.lower()
            for p in c['solution_container_patterns']:
                require(p not in low, f'CLOSED-BOOK-CONTAINER: {rel} contains forbidden solution marker {p!r}')

def validate_pedagogy() -> None:
    c=json.loads((ROOT/'scripts/pedagogy_contract.json').read_text(encoding='utf-8'))
    for skill,e in c['events'].items():
        x,u,a=e['explanation']['order'],e['required_use']['order'],e['assessment']['order']
        require(x<u<a, f'PEDAGOGY-ORDER {skill}: expected explanation < required use < assessment, got {x},{u},{a}')
        for kind in ('explanation','required_use','assessment'):
            source=e[kind]['source']
            src, sep, anchor = source.partition('#')
            require((ROOT/src).is_file(), f'PEDAGOGY-SOURCE {skill}: missing {src}')
            if sep:
                body=(ROOT/src).read_text(encoding='utf-8')
                explicit=set(re.findall(r'<a id="([^"]+)"',body))
                headings={slug(h) for h in re.findall(r'^#{1,6}\s+(.+)$',body,re.M)}
                require(anchor in explicit|headings, f'LINK-ANCHOR: pedagogy source {source} missing')
    d10=(ROOT/'docs/day_10_learning_path.md').read_text(encoding='utf-8').lower()
    required=(ROOT/'docs/tasks/spring-01/01-14-garden.md').read_text(encoding='utf-8').lower()
    require('mov ecx, edx' in d10 and 'neg ecx' in d10 and 'or ecx, edx' in d10 and 'shr ecx, 31' in d10, 'PEDAGOGY-CEIL: complete branchless nonzero explanation missing before use')
    code = '\n'.join(re.findall(r'```asm[^\n]*\n(.*?)```', required, flags=re.S | re.I))
    for forbidden in ('setnz','sete ','cmov','jz ','jnz '):
        require(forbidden not in code, f'PEDAGOGY-FUTURE-DEPENDENCY: garden requires forbidden mechanism {forbidden.strip()}')

def validate_transfers() -> None:
    c=json.loads((ROOT/'scripts/transfer_contract.json').read_text(encoding='utf-8'))
    task_text=(ROOT/'docs/transfer_workbook.md').read_text(encoding='utf-8')
    key_text=(ROOT/'docs/transfer_keys.md').read_text(encoding='utf-8')
    ids=list(c['tasks'])
    for tid in ids:
        ts=exact_anchor_section(task_text,tid.lower())
        ks=exact_anchor_section(key_text,'key-'+tid.lower())
        td=c['tasks'][tid]
        require(hashlib.sha256(norm(ts).encode()).hexdigest()==td['task_fingerprint'], f'TRANSFER-SYNC {tid}: task changed without contract update')
        require(hashlib.sha256(norm(ks).encode()).hexdigest()==td['key_fingerprint'], f'TRANSFER-SYNC {tid}: key changed without contract update')
        low=ts.lower()
        for feature in td['required_features']:
            require(feature.lower() in low, f'TRANSFER-STRUCTURE {tid}: missing required structural feature {feature}')
        for banned in td['banned_old_fragments']:
            require(norm(banned) not in norm(ts), f'TRANSFER-OLD {tid}: old copyable fragment returned: {banned}')
        if td.get('requires_diagnostic_counterexample'):
            require('контрпример' in ks.lower(), f'TRANSFER-DIAGNOSTIC {tid}: key lacks a diagnostic counterexample')

def all_return_paths_restore(text: str, reg: str) -> bool:
    lines=[]
    for raw in strip_comments(text).splitlines():
        line=raw.strip().lower()
        if line: lines.append(line)
    pushes=sum(line==f'push {reg}' for line in lines)
    if pushes!=1: return False
    for i,line in enumerate(lines):
        if line=='ret':
            j=i-1
            seen=False
            while j>=0 and not lines[j].endswith(':'):
                if lines[j]==f'pop {reg}': seen=True; break
                j-=1
            if not seen: return False
    return True

def validate_asm() -> None:
    c=json.loads((ROOT/'scripts/executable_contract.json').read_text(encoding='utf-8'))
    allowed={'TRACE_ONLY','FRAGMENT','COMPILE','RUN','NEGATIVE','PSEUDOCODE'}
    classified=set(c['blocks'])
    actual={str(p.relative_to(ROOT)) for p in (ROOT/'examples').glob('*.asm')}
    missing=sorted(actual-classified)
    stale=sorted(classified-actual)
    require(not missing,f'ASM-BLOCK-COVERAGE: unclassified examples: {missing}')
    require(not stale,f'ASM-BLOCK-COVERAGE: contract points to missing examples: {stale}')
    for rel,bd in c['blocks'].items():
        p=ROOT/rel; require(p.is_file(),f'ASM-BLOCK: missing {rel}')
        text=p.read_text(encoding='utf-8'); require(bd['class'] in allowed,f'ASM-BLOCK: invalid class {bd["class"]}')
        require(f'; BLOCK: {bd["class"]}' in text,f'ASM-BLOCK: {rel} lacks explicit classification')
        if bd['class']=='RUN': require((ROOT/bd['golden']).is_file(),f'ASM-GOLDEN: {rel} lacks expected output')
    ceil=(ROOT/'examples/10_branchless_ceil.asm').read_text(encoding='utf-8').lower()
    for needle in ('xor edx, edx','div ecx','mov ecx, edx','neg ecx','or ecx, edx','shr ecx, 31','add eax, ecx'):
        require(needle in ceil,f'ASM-CEIL: missing {needle}')
    idiv=(ROOT/'examples/11_idiv_overflow_negative.asm').read_text(encoding='utf-8').lower()
    require('cdq' in idiv,'ASM-IDIV-CDQ: signed division fixture lost cdq')
    require(re.search(r'\bidiv\s+(?![-+]?\d)',idiv) is not None,'ASM-IDIV-OPERAND: idiv must use r/m operand, not immediate')
    scanf=(ROOT/'examples/14_scanf_call.asm').read_text(encoding='utf-8').lower()
    require('sub esp, 8' in scanf and 'add esp, 16' in scanf,'ASM-CALL-AREA: scanf padding/cleanup mismatch')
    require(re.search(r'push\s+x\b',scanf) is not None and 'push dword [x]' not in scanf and 'push [x]' not in scanf,'ASM-SCANF-ADDRESS: scanf must receive x address, not [x] value')
    cs=(ROOT/'examples/12_callee_saved.asm').read_text(encoding='utf-8')
    require(all_return_paths_restore(cs,'esi'),'ASM-CALLEE-SAVED: esi is not restored on every return path')
    x87=(ROOT/'examples/13_x87_order.asm').read_text(encoding='utf-8').lower()
    require('fsubp st1, st0' in x87,'ASM-X87-SUB: wrong fsubp direction')
    require('fdivp st1, st0' in x87,'ASM-X87-DIV: wrong fdivp direction')
    absx=(ROOT/'examples/04_branchless_abs.asm').read_text(encoding='utf-8')
    require('eax != 0x80000000' in absx or 'uint32' in absx.lower(),'ASM-ABS-CONTRACT: INT32_MIN boundary is not stated')

def validate_manifest() -> None:
    import importlib.util
    spec=importlib.util.spec_from_file_location('course_manifest',ROOT/'scripts/course_manifest.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    required={'docs/prerequisite_refreshers.md','docs/day_25.md','docs/final_exam.md','docs/final_exam_keys.md','docs/final_remediation.md'}
    require(required <= set(mod.STANDALONE_RELATIVE_PATHS), 'MANIFEST-STANDALONE: prerequisite refreshers/final route missing')
    expected_generated={'docs/textbook.md','docs/course_migration.md','docs/closed_book_workbook.md','docs/generated_source_manifest.json'}
    require(set(mod.GENERATED_RELATIVE_PATHS)==expected_generated,'MANIFEST-GENERATED: generated owner set changed')
    for rel in expected_generated:
        require((ROOT/rel).is_file(),f'MANIFEST-GENERATED-MISSING: {rel}')
    manifest=json.loads((ROOT/'docs/generated_source_manifest.json').read_text(encoding='utf-8'))
    require(bool(manifest.get('source_tree_sha256')),'MANIFEST-PROVENANCE: source tree digest missing')
    for rel,digest in manifest.get('generated',{}).items():
        require((ROOT/rel).is_file(),f'MANIFEST-PROVENANCE: generated file missing: {rel}')
        actual=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
        require(actual==digest,f'MANIFEST-PROVENANCE: digest mismatch for {rel}')

def validate_docs_contract() -> None:
    c=json.loads((ROOT/'scripts/assessment_contract.json').read_text(encoding='utf-8'))
    docs=(ROOT/'docs/day_25.md').read_text(encoding='utf-8')
    f=c['assessments']['FINAL']
    for marker in (f'**{f["maximum"]}**',f'**{f["threshold"]}**',f'**{f["duration_minutes"]} минут**'):
        require(marker in docs,f'DOCS-ASSESSMENT: day_25 missing synchronized marker {marker}')
    for b,bd in f['block_minimums'].items():
        require(f'| {b} |' in docs and f'| {bd["minimum"]} |' in docs,f'DOCS-ASSESSMENT: block {b} minimum not synchronized')
    require('CP1 + CP2 + CP3 + CP4 + CP5 + CP6 + FINAL' in docs,'DOCS-READINESS: readiness composition missing')

def slug(s: str) -> str:
    s=s.strip().lower()
    s=re.sub(r'[`*_]','',s)
    s=re.sub(r'[^\w\-а-яё ]+','',s,flags=re.I)
    return re.sub(r'\s+','-',s)

def validate_links() -> None:
    md=list((ROOT/'docs').rglob('*.md'))
    routes={'/'+str(p.relative_to(ROOT/'docs').with_suffix('')).replace('index','').rstrip('/') for p in md}
    anchors={}
    for p in md:
        txt=p.read_text(encoding='utf-8')
        aset=set(re.findall(r'<a id="([^"]+)"',txt))
        aset.update(slug(h) for h in re.findall(r'^#{1,6}\s+(.+)$',txt,re.M))
        anchors['/'+str(p.relative_to(ROOT/'docs').with_suffix('')).replace('index','').rstrip('/')]=aset
    for p in md:
        txt=p.read_text(encoding='utf-8')
        for target in re.findall(r'\]\((/[^)]+)\)',txt):
            route,_,anchor=target.partition('#')
            require(route in routes,f'LINK-ROUTE: {p.relative_to(ROOT)} -> {route} missing')
            if anchor: require(anchor in anchors.get(route,set()),f'LINK-ANCHOR: {p.relative_to(ROOT)} -> {target} missing')
    startup=(ROOT/'docs/instruction_reference.md').read_text(encoding='utf-8')
    require('exec → loader → _start → runtime startup → main → exit' in startup,'STARTUP-DIRECTION: startup/runtime/main direction reversed or missing')

def main() -> int:
    checks=[validate_leakage,validate_pedagogy,validate_transfers,validate_asm,validate_manifest,validate_docs_contract,validate_links]
    try:
        for fn in checks:
            fn(); print(fn.__name__.upper()+'=PASS')
    except (VError,ValueError,KeyError,OSError) as exc:
        print(str(exc),file=sys.stderr); return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
