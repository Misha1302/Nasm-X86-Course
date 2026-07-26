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

# Replace the stale pre-ID workbook anchor.
day10_path = DOCS / "day_10_learning_path.md"
day10 = day10_path.read_text(encoding="utf-8")
old_anchor = "](/transfer_workbook#день-10-биты-и-branchless)"
new_anchor = "](/transfer_workbook#tr-10)"
if old_anchor not in day10:
    raise SystemExit("expected stale Day 10 workbook anchor was not found")
day10_path.write_text(day10.replace(old_anchor, new_anchor), encoding="utf-8")


def insert_invariants(path: Path, mapping: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^### ([A-Z0-9-]+)\s*$", text))
    for identifier, invariant in mapping.items():
        heading = next((match for match in headings if match.group(1) == identifier), None)
        if heading is None:
            raise SystemExit(f"missing key section {identifier} in {path}")
        next_heading = next((match for match in headings if match.start() > heading.start()), None)
        end = next_heading.start() if next_heading else len(text)
        section = text[heading.start():end]
        if "**Инвариант:**" in section:
            continue
        first_bullet = re.search(r"(?m)^- \*\*[^\n]+$", section)
        if first_bullet is None:
            raise SystemExit(f"no insertion point for {identifier} in {path}")
        insertion = first_bullet.end()
        section = section[:insertion] + f"\n- **Инвариант:** {invariant}" + section[insertion:]
        text = text[:heading.start()] + section + text[end:]
        headings = list(re.finditer(r"(?m)^### ([A-Z0-9-]+)\s*$", text))
    path.write_text(text, encoding="utf-8")


insert_invariants(
    DOCS / "checkpoint_keys.md",
    {
        "CP1-SIZE-R": "размер destination определяет, какая часть регистра изменяется; инструкция не обязана определять старшие биты.",
        "CP1-SIZE-W": "ширина memory write является частью семантики и границы соседних объектов.",
        "CP5-FP-BINARY": "веса дробных binary-позиций равны степеням 1/2.",
        "CP5-FP-REPR": "конечная binary fraction после сокращения имеет denominator степени 2.",
        "CP5-STARTUP": "ELF entry point и exported symbol main являются разными контрактами.",
        "CP5-SAFETY": "undefined behavior не обещает ни crash, ни продолжение; наблюдаемое отсутствие падения не доказывает корректность.",
        "CP5-NAN": "NaN создаёт unordered comparison и не ведёт себя как обычная константа.",
        "CP6-THIS": "machine offsets доказывают обращения к памяти, но не high-level names или тип base pointer.",
        "CP6-OBJECT": "object data, dispatch metadata и method code принадлежат разным слоям модели.",
        "CP6-CALLS": "directness определяется местом хранения target address, а virtual semantics требует дополнительного ABI evidence.",
    },
)
insert_invariants(
    DOCS / "transfer_keys.md",
    {
        "TR-24": "indirect call shape является фактом; this/vptr/virtual interpretation остаётся ABI-гипотезой.",
    },
)

print(
    f"Updated {changed_files} day files; "
    f"normalized {replaced_checklist_items} checklist items; "
    f"added {added_next_steps} next-step sections; "
    "fixed key invariants and Day 10 anchor"
)
