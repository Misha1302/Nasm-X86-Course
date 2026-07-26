#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("apply_review_remediation.py")
text = path.read_text(encoding="utf-8")
old = "('docs/day_06.md', '## Зачем этот день',"
new = "('docs/day_06.md', '## За 30 секунд',"
if text.count(old) != 1:
    raise SystemExit(f"expected one Day 06 insertion marker, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
