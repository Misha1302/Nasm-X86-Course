#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

changed_files = 0
replaced_checklist_items = 0
added_next_steps = 0

for day in range(1, 26):
    path = DOCS / f"day_{day:02d}.md"
    text = path.read_text(encoding="utf-8")
    original = text

    checklist_match = re.search(r"(?m)^## Чеклист\s*$", text)
    if checklist_match is None:
        raise SystemExit(f"missing checklist heading: {path}")

    checklist_start = checklist_match.end()
    next_h2 = re.search(r"(?m)^## (?!Чеклист).+$", text[checklist_start:])
    checklist_end = checklist_start + next_h2.start() if next_h2 else len(text)
    checklist = text[checklist_start:checklist_end]

    normalized_lines: list[str] = []
    for line in checklist.splitlines():
        updated = line
        if re.match(r"^\s*- \[ \] ", line):
            updated, count = re.subn(r"\bпонимать\b", "объяснить", updated, count=1, flags=re.I)
            replaced_checklist_items += count
            updated, count = re.subn(r"\bпонять\b", "объяснить", updated, count=1, flags=re.I)
            replaced_checklist_items += count
        normalized_lines.append(updated)
    normalized = "\n".join(normalized_lines)
    if checklist.endswith("\n"):
        normalized += "\n"
    text = text[:checklist_start] + normalized + text[checklist_end:]

    if not re.search(r"(?m)^## Следующий шаг\s*$", text):
        block = f"""

---

## Следующий шаг

1. Реши [TR-{day:02d} в рабочей тетради](/transfer_workbook#tr-{day:02d}) без просмотра ответа.
2. После законченной попытки открой [диагностический ключ TR-{day:02d}](/transfer_keys#key-tr-{day:02d}).
3. Запиши нарушенный инвариант и минимальный контрпример в журнал ошибок.
4. Если модель верна — переходи дальше; если нет — вернись к указанному prerequisite и затем реши новый вариант.
"""
        text = text.rstrip() + block
        added_next_steps += 1

    text = text.rstrip() + "\n"
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed_files += 1

if added_next_steps != 25:
    raise SystemExit(f"expected to add 25 next-step sections, added {added_next_steps}")
if replaced_checklist_items == 0:
    raise SystemExit("expected at least one non-observable checklist item to normalize")

print(
    f"Updated {changed_files} day files; "
    f"normalized {replaced_checklist_items} checklist items; "
    f"added {added_next_steps} next-step sections"
)
