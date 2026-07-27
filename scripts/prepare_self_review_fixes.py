#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("apply_self_review_fixes.py")
text = path.read_text(encoding="utf-8")
old = 'r"(?P<i>^[ \\t]*)push (?P<reg>eax|ecx|edx)\\s*(?P<c>;[^\\n]*)?\\n"'
new = 'r"(?P<i>^[ \\t]*)push (?P<reg>eax|ecx|edx)[ \\t]*(?P<c>;[^\\n]*)?\\n"'
count = text.count(old)
if count != 1:
    raise SystemExit(f"saved-value matcher: expected one occurrence, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
