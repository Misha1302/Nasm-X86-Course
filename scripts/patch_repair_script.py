#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/apply_course_repairs.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        r'''raise SystemExit("Course validation failed:\n- " + "\n- ".join(errors))''',
        r'''raise SystemExit("Course validation failed:\\n- " + "\\n- ".join(errors))''',
        "validator escaping",
    ),
    (
        r'''re.findall(r'link:\s*"(/[^"]+)"', config)''',
        r'''re.findall(r'link:\\s*"(/[^"]+)"', config)''',
        "regex escaping",
    ),
    (
        "Формула `(a + b - 1) / b` корректна только когда промежуточное `a + b - 1` помещается в 32 бита.",
        "Промежуточное `a + b - 1` может переполниться. Формула `(a + b - 1) / b` корректна только когда этот результат помещается в 32 бита.",
        "ceil overflow wording",
    ),
    (
        'for stem, output in expected.items():\n    write(f"examples/expected/{stem}.txt", output)',
        'for stem, output in expected.items():\n    target = ROOT / "examples" / "expected" / f"{stem}.txt"\n    target.parent.mkdir(parents=True, exist_ok=True)\n    target.write_text(output, encoding="utf-8")',
        "empty golden output",
    ),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one source match, got {count}")
    text = text.replace(old, new, 1)

gdb_count = text.count("```gdb")
if gdb_count == 0:
    raise SystemExit("GDB fence patch: no source matches")
text = text.replace("```gdb", "```text")

if 'target.write_text(output, encoding="utf-8")' not in text:
    raise SystemExit("golden output patch did not apply")

path.write_text(text, encoding="utf-8")
Path("repair-failure.log").unlink(missing_ok=True)
Path(__file__).unlink()
