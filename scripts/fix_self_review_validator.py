#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("validate_course.py")
text = path.read_text(encoding="utf-8")
old = r'r"push (eax|ecx|edx).*?sub esp, 8.*?call printf.*?add esp, 16.*?pop \\1"'
new = r'r"push (eax|ecx|edx).*?sub esp, 8.*?call printf.*?add esp, 16.*?pop \1"'
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one escaped backreference, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
