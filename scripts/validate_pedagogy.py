#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
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


# Files that make learner assumptions and terminology explicit.
prerequisites = read("docs/prerequisites.md")
glossary = read("docs/glossary.md")
self_study = read("docs/self_study.md")
course_style = read("docs/course_style.md")

for marker in (
    "Терминал",
    "C++: указатель",
    "C++: структура",
    "Решение о старте",
):
    if marker not in prerequisites:
        errors.append(f"prerequisites lack marker {marker!r}")

for marker in (
    "### Инвариант",
    "### Контрпример",
    "### Адрес",
    "### ABI",
    "### x87",
):
    if marker not in glossary:
        errors.append(f"glossary lacks marker {marker!r}")

if "условие, которое должно оставаться истинным" not in self_study:
    errors.append("self_study does not explain 'инвариант' in learner language")
if "обязательный термин вводится до использования" not in course_style.lower():
    errors.append("course_style lacks first-use terminology rule")


# Protect machine-readable VitePress syntax from prose translation.
index = read("docs/index.md")
frontmatter = "\n".join(index.splitlines()[:20])
if "layout: home" not in frontmatter:
    errors.append("docs/index.md must preserve the VitePress key 'layout: home'")
if re.search(r"(?m)^\s*расположение\s*:\s*home\s*$", frontmatter):
    errors.append("docs/index.md contains a translated VitePress key")


# Known mechanical-translation failures. These exact strings are never valid prose.
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
)
for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for phrase in banned_phrases:
        if phrase in text:
            errors.append(f"mechanical-translation phrase {phrase!r}: {path.relative_to(ROOT)}")


# Day 05 owns address/value, not stack or ABI mechanics.
day05 = read("docs/day_05.md")
for forbidden in ("call scanf", "call printf", "sub esp", "and esp, -16"):
    if forbidden in day05:
        errors.append(f"day_05 introduces call-stack mechanics too early: {forbidden!r}")
for marker in ("адрес", "значение", "lea", "little-endian", "В этой главе стек и ABI не требуются"):
    if marker not in day05:
        errors.append(f"day_05 lacks boundary marker {marker!r}")


# Day 06 must give one internally consistent call-area model.
day06 = read("docs/day_06.md")
for marker in (
    "минимальная и достаточная модель",
    "всю область вызова",
    "8 байт выравнивания + 8 байт аргументов",
    "add esp, 16",
    "eax, ecx, edx",
):
    if marker not in day06:
        errors.append(f"day_06 lacks call-area marker {marker!r}")
if "Почему после вызова `add esp, 8`" in day06:
    errors.append("day_06 restores the old contradictory cleanup section")

# A two-argument aligned call must clean 16 bytes in the same fenced fragment.
for block in re.findall(r"```asm\n(.*?)```", day06, flags=re.S):
    if "sub esp, 8" in block and block.count("push ") >= 2 and "call " in block:
        if "add esp, 16" not in block:
            errors.append("day_06 has a two-argument aligned call without add esp,16")


# Later stack chapters must agree with the early call-area model.
day16 = read("docs/day_16.md")
if "8 байт выравнивания + 8 байт аргументов = 16 байт" not in day16:
    errors.append("day_16 does not reconcile the Day 06 call area")
if "Нельзя заменить эту очистку на `add esp,8`" not in day16:
    errors.append("day_16 lacks the cleanup counterexample")

day23 = read("docs/day_23.md")
for marker in (
    "два разных стека",
    "4 padding + 8 bytes for double",
    "add esp, 16",
    "глубина x87",
):
    if marker.lower() not in day23.lower():
        errors.append(f"day_23 lacks two-stack marker {marker!r}")


# Day 10 is a module, not one overloaded sitting.
day10_path = read("docs/day_10_learning_path.md")
for letter in "ABCDEF":
    if f"Сессия 10{letter}" not in day10_path:
        errors.append(f"day_10_learning_path lacks Session 10{letter}")
if "не является обязательной" not in day10_path:
    errors.append("Day 10 challenge is not separated from the mandatory core")


# Navigation must expose the learner-facing support pages.
config = read("docs/.vitepress/config.mts")
for link in ("/prerequisites", "/glossary", "/self_study", "/day_10_learning_path"):
    if f'link: "{link}"' not in config:
        errors.append(f"VitePress navigation lacks {link}")

readme = read("README.md")
for link in ("docs/prerequisites.md", "docs/glossary.md", "docs/self_study.md"):
    if link not in readme:
        errors.append(f"README lacks {link}")


if errors:
    print("Pedagogical validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Pedagogical validation passed")
