#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("apply_review_remediation.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        "('docs/day_06.md', '## Зачем этот день',",
        "('docs/day_06.md', '## За 30 секунд',",
        "Day 06 insertion marker",
    ),
    (
        "generator = '''#!/usr/bin/env python3",
        "generator = r'''#!/usr/bin/env python3",
        "embedded generator raw string",
    ),
    (
        '''for index, block in enumerate(prompt_blocks, start=1):
    for tag in ("task", "chapter", "answer"):
        if block.count(f"<{tag}>") != 1 or block.count(f"</{tag}>") != 1:
            errors.append(f"AI prompt block {index} has invalid <{tag}> contract")''',
        '''for index, block in enumerate(prompt_blocks, start=1):
    contract = re.search(
        r"(?s)<task>\\s*.*?</task>\\s*<chapter>\\s*.*?</chapter>\\s*<answer>\\s*.*?</answer>\\s*$",
        block,
    )
    if contract is None:
        errors.append(f"AI prompt block {index} lacks a terminal task/chapter/answer contract")''',
        "per-prompt terminal contract parser",
    ),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    text = text.replace(old, new, 1)

x87_old = "fstp qword [esp + 4]"
x87_count = text.count(x87_old)
if x87_count < 2:
    raise SystemExit(f"x87 argument placement: expected at least two occurrences, found {x87_count}")
text = text.replace(x87_old, "fstp qword [esp]")
text = text.replace(
    '`[esp+4..esp+11]` содержит 8-byte `double`, а `push fmtFloat` кладёт первый аргумент перед ним.',
    '`[esp..esp+7]` содержит `double` до `push`; после `push fmtFloat` он непрерывно лежит по `[esp+4..esp+11]`, а padding остаётся выше всех аргументов.',
)

needle = '''    text = text.replace(
        'for generated in (DOCS / "textbook.md", DOCS / "course_migration.md"):',
'''
injected = '''    text = text.replace(
        'if len(rows) != 25 or any("| standalone | 6/6 |" not in row for row in rows):',
        'if len(rows) != 25 or any("| structural-6/6 | 6/6 |" not in row for row in rows):',
    )
''' + needle
count = text.count(needle)
if count != 1:
    raise SystemExit(f"standalone smoke-check injection: expected one occurrence, found {count}")
text = text.replace(needle, injected, 1)

validator_marker = 'day22_text = (DOCS / "day_22.md").read_text(encoding="utf-8")'
validator_injection = '''for path in [*(ROOT / "examples").glob("*.asm"), *DOCS.rglob("*.md")]:
    source = path.read_text(encoding="utf-8")
    if re.search(r"sub esp,\\s*12.*?fstp qword \\[esp \\+ 4\\].*?push .*?call printf", source, flags=re.S | re.I):
        errors.append(f"x87 variadic padding splits arguments in {path.relative_to(ROOT)}")


''' + validator_marker
count = text.count(validator_marker)
if count != 1:
    raise SystemExit(f"x87 validator injection: expected one occurrence, found {count}")
text = text.replace(validator_marker, validator_injection, 1)

path.write_text(text, encoding="utf-8")
