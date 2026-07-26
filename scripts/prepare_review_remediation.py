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

path.write_text(text, encoding="utf-8")
