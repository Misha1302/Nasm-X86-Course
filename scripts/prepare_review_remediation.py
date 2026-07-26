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
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
