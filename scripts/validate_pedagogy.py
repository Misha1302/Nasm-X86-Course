#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
errors: list[str] = []


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing required pedagogical file: {relative}")
        return ""
    return path.read_text(encoding="utf-8")


def require(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        errors.append(f"{owner} lacks marker {marker!r}")


def forbid(text: str, marker: str, owner: str) -> None:
    if marker in text:
        errors.append(f"{owner} contains forbidden marker {marker!r}")


prerequisites = read("docs/prerequisites.md")
refreshers = read("docs/prerequisite_refreshers.md")
glossary = read("docs/glossary.md")
self_study = read("docs/self_study.md")
walkthroughs = read("docs/transfer_walkthroughs.md")
course_style = read("docs/course_style.md")
readme = read("README.md")

# Entry contract and real recovery routes.
for marker in (
    "Терминал",
    "C++: указатель",
    "C++: массив",
    "C++: структура",
    "Решение о старте",
    "/prerequisite_refreshers#терминал-и-файлы",
    "/prerequisite_refreshers#указатели-c",
    "/prerequisite_refreshers#массивы-c",
    "/prerequisite_refreshers#структуры-c",
):
    require(prerequisites, marker, "prerequisites")

for marker in (
    "## Терминал и файлы",
    "## Двоичная запись и размеры",
    "## Указатели C++",
    "## Массивы C++",
    "## Структуры C++",
    "## Научная запись",
):
    require(refreshers, marker, "prerequisite_refreshers")

# Terms needed by TR-01 and later diagnostics.
for marker in (
    "### Ассемблер",
    "### Объектный файл",
    "### Компоновщик",
    "### Исполняемый файл",
    "### ELF",
    "### Символ",
    "### Запись перемещения",
    "### Загрузчик",
    "### Процесс",
    "### Адрес",
    "### Инвариант",
    "### Контрпример",
    "### ABI",
    "### x87",
):
    require(glossary, marker, "glossary")

for marker in (
    "компоновщик",
    "объектный файл",
    "загрузчик",
    "Запись перемещения",
    "Центральный инвариант",
):
    require(read("docs/day_01.md"), marker, "day_01")

# Staged diagnostics for difficult tasks.
for marker in (
    "TR-13",
    "TR-17",
    "TR-23",
    "### Направляющий вопрос",
    "### Новый вариант",
):
    require(walkthroughs, marker, "transfer_walkthroughs")
require(self_study, "/transfer_walkthroughs", "self_study")
require(self_study, "краткий диагностический ключ", "self_study")
require(self_study, "пошаговый разбор", "self_study")

# Protect machine-readable VitePress syntax.
index = read("docs/index.md")
frontmatter = "\n".join(index.splitlines()[:20])
require(frontmatter, "layout: home", "docs/index.md frontmatter")
forbid(frontmatter, "расположение: home", "docs/index.md frontmatter")

# Known mechanical-translation failures.
banned_phrases = (
    "знаковая/беззнаковая интерпретация интерпретацию",
    "регистр знает знаковая/беззнаковая",
    "В построчное расположение",
    "Возможный расположение",
    "переход к следующему узлу связный список",
    "стартовый код-код",
    "подготавливает вызов среда выполнения",
    "различить назначения канарейку",
    "с расположение данных в кадре стека",
    "сложные оптимизации анализ совпадения адресов",
    "address return",
)
for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for phrase in banned_phrases:
        if phrase in text:
            errors.append(f"mechanical-translation phrase {phrase!r}: {path.relative_to(ROOT)}")

# Day 05 owns address/value, not stack mechanics.
day05 = read("docs/day_05.md")
for forbidden in ("call scanf", "call printf", "sub esp", "and esp, -16"):
    forbid(day05, forbidden, "day_05")
for marker in ("адрес", "значение", "lea", "little-endian", "В этой главе стек и ABI не требуются"):
    require(day05, marker, "day_05")

# One ABI owner and one formula.
alignment = read("docs/patterns/libc_alignment.md")
c_abi = read("docs/c_abi.md")
day06 = read("docs/day_06.md")
day16 = read("docs/day_16.md")
day17 = read("docs/day_17.md")
day23 = read("docs/day_23.md")
patterns = read("docs/code_patterns.md")

for marker in (
    "padding = (16 - (argument_bytes % 16)) % 16",
    "После возврата вызывающая функция обязана восстановить `esp`",
):
    require(alignment, marker, "libc_alignment")

for marker in (
    "argument_bytes = сумма размеров аргументов",
    "padding        = (16 - argument_bytes % 16) % 16",
    "cleanup        = padding + argument_bytes",
    "адрес возврата",
):
    require(c_abi, marker, "c_abi")

for owner, text in (
    ("day_06", day06),
    ("day_16", day16),
    ("day_17", day17),
    ("day_23", day23),
    ("c_abi", c_abi),
    ("code_patterns", patterns),
):
    require(text, "add esp, 16", owner)

for owner, text in (("day_17", day17), ("code_patterns", patterns), ("c_abi", c_abi)):
    require(text, "sub esp, 8", owner)
    require(text, "push dword [b]", owner)
    require(text, "push dword [a]", owner)
    require(text, "add esp, 16", owner)

contract_drift = (
    "bytes_to_remove = argument_count * 4",
    "Почему `add esp, 8`?",
    "| `printf(\"%d\", x)` | `add esp, 8` |",
    "| `scanf(\"%d%d\", &a, &b)` | `add esp, 12` |",
    "caller removes 2 arguments * 4 bytes",
)
for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for phrase in contract_drift:
        if phrase in text:
            errors.append(f"ABI contract drift {phrase!r}: {path.relative_to(ROOT)}")

# Canonical Day 10 structure. Legacy anchors must point to matching visible sessions.
day10 = read("docs/day_10.md")
day10_path = read("docs/day_10_learning_path.md")
for marker in (
    "10A | побитовые операции и слияние по маске",
    "10B | маска `0/-1` и выбор без переходов",
    "10C | безопасное округление вверх",
    "10D | задача 01-14",
    "10E | задача 01-15",
    "10F | задача 01-16",
    "Обязательное ядро — сессии 10A–10E",
):
    require(day10, marker, "day_10")

for marker in (
    "## Сессия 10A — побитовые операции и слияние по маске",
    "## Сессия 10B — маска `0/-1` и выбор без переходов",
    "## Сессия 10C — безопасное округление вверх",
    "## Сессия 10D — задача 01-14",
    "## Сессия 10E — задача 01-15",
    "## Сессия 10F — challenge 01-16",
    'id="сессия-10b-маска-0-1-и-выбор-без-ветвлений"',
    'id="сессия-10c-ceil-и-деление"',
):
    require(day10_path, marker, "day_10_learning_path")
forbid(day10_path, "Этот явный якорь сохраняет старые ссылки", "day_10_learning_path")

# Later chapters must expose exact prerequisite recovery.
day15 = read("docs/day_15.md")
day19 = read("docs/day_19.md")
require(day15, "/prerequisite_refreshers#массивы-c", "day_15")
require(day19, "/prerequisite_refreshers#указатели-c", "day_19")
require(day19, "/prerequisite_refreshers#структуры-c", "day_19")

# Keep selected learner-facing pages consistently Russian outside code identifiers.
for owner, text in (
    ("day_15", day15),
    ("day_19", day19),
    ("day_20", read("docs/day_20.md")),
    ("day_21", read("docs/day_21.md")),
):
    for phrase in ("frame layout", "linked list", "offsets", "address return"):
        forbid(text, phrase, owner)

# Navigation from the repository entry point.
for link in (
    "docs/prerequisites.md",
    "docs/prerequisite_refreshers.md",
    "docs/glossary.md",
    "docs/self_study.md",
    "docs/transfer_walkthroughs.md",
):
    require(readme, link, "README")

if "условие, которое должно оставаться истинным" not in self_study:
    errors.append("self_study does not explain 'инвариант' in learner language")
if "обязательный термин вводится до использования" not in course_style.lower():
    errors.append("course_style lacks first-use terminology rule")

if errors:
    print("Pedagogical validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Pedagogical validation passed")
