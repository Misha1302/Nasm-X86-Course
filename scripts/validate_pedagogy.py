#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import re
import sys

from course_manifest import STANDALONE_RELATIVE_PATHS

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
errors: list[str] = []


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing required file: {relative}")
        return ""
    return path.read_text(encoding="utf-8")


def require(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        errors.append(f"{owner} lacks marker {marker!r}")


def forbid(text: str, marker: str, owner: str) -> None:
    if marker in text:
        errors.append(f"{owner} contains forbidden marker {marker!r}")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def heading_ids(text: str, prefix: str) -> list[str]:
    return re.findall(rf"(?m)^### ({re.escape(prefix)}[A-Z0-9-]+)\b", text)


def level2_sections(text: str, prefix: str) -> dict[int, str]:
    matches = list(re.finditer(rf"(?m)^## {re.escape(prefix)}(\d+)[^\n]*$", text))
    result: dict[int, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[int(match.group(1))] = text[match.start():end]
    return result


assessment_path = ROOT / "scripts" / "assessment_contract.json"
try:
    assessment = json.loads(assessment_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError) as exc:
    errors.append(f"invalid assessment contract: {exc}")
    assessment = {"checkpoints": {}, "final_exam": {}, "day10": {}}

# Full standalone export must include every learner-critical owner.
required_sources = {
    "docs/prerequisites.md",
    "docs/prerequisite_refreshers.md",
    "docs/glossary.md",
    "docs/self_study.md",
    "docs/support_matrix.md",
    "docs/c_abi.md",
    "docs/patterns/libc_alignment.md",
    "docs/transfer_walkthroughs.md",
    "docs/day_25.md",
    "docs/final_exam.md",
    "docs/final_exam_keys.md",
    "docs/final_remediation.md",
}
manifest_sources = set(STANDALONE_RELATIVE_PATHS)
for source in sorted(required_sources - manifest_sources):
    errors.append(f"standalone manifest lacks learner-critical source: {source}")
for source in STANDALONE_RELATIVE_PATHS:
    if not (ROOT / source).is_file():
        errors.append(f"standalone source does not exist: {source}")

textbook = read("docs/textbook.md")
for source in STANDALONE_RELATIVE_PATHS:
    require(textbook, f"<!-- source: {source} -->", "generated textbook")

# Closed-book artifact must hide all solution containers, regardless of labels.
closed = read("docs/closed_book_workbook.md")
for marker in ("<details", "</details>", "<summary>"):
    forbid(closed.lower(), marker, "closed_book_workbook")
require(closed, "<!-- source-final-exam: docs/final_exam.md -->", "closed_book_workbook")

closed_norm = normalize(closed)
for day in range(1, 26):
    source = read(f"docs/day_{day:02d}.md")
    for body in re.findall(r"(?is)<details(?:\s[^>]*)?>(.*?)</details>", source):
        body = re.sub(r"(?is)<summary>.*?</summary>", "", body)
        candidate = normalize(body)
        if len(candidate) >= 80 and candidate in closed_norm:
            errors.append(f"closed-book artifact leaks a solution body from day_{day:02d}")
            break

# One executable ABI model. Abstract call/ret exercises must label themselves.
day25 = read("docs/day_25.md")
final_exam = read("docs/final_exam.md")
final_keys = read("docs/final_exam_keys.md")
instruction_reference = read("docs/instruction_reference.md")
transfer_workbook = read("docs/transfer_workbook.md")
transfer_keys = read("docs/transfer_keys.md")
checkpoints = read("docs/checkpoints.md")
checkpoint_keys = read("docs/checkpoint_keys.md")
example_sum = read("examples/09_aligned_sum_call.asm")

correct_sum_call = "sub esp, 8\npush dword [b]\npush dword [a]\ncall sum\nadd esp, 16"
for owner, text in (
    ("day_25", day25),
    ("final_exam_keys", final_keys),
    ("instruction_reference", instruction_reference),
):
    require(text, correct_sum_call, owner)

require(example_sum, "sub esp, 8", "aligned sum example")
require(example_sum, "call sum", "aligned sum example")
require(example_sum, "add esp, 16", "aligned sum example")

old_sum_pattern = re.compile(
    r"push(?:\s+dword)?\s+\[?b\]?\s*\n"
    r"push(?:\s+dword)?\s+\[?a\]?\s*\n"
    r"call\s+sum\s*\n"
    r"add\s+esp,\s*8\b",
    flags=re.I,
)
for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    if old_sum_pattern.search(text):
        errors.append(f"stale unaligned sum call: {path.relative_to(ROOT)}")

for owner, text in (
    ("transfer_workbook TR-16", transfer_workbook),
    ("transfer_keys TR-16", transfer_keys),
    ("checkpoint CP4", checkpoints),
):
    require(text, "абстракт", owner.lower())

# x87 reference must state operand direction rather than vague 'top elements'.
for marker in (
    "fsubp st1,st0` | `st(1)=st(1)-st(0)`",
    "fdivp st1,st0` | `st(1)=st(1)/st(0)`",
):
    require(instruction_reference, marker, "instruction_reference")

# Day 10 mandatory/optional contract must match checkpoint and final assessment.
cp2 = level2_sections(checkpoints, "Контрольная точка ").get(2, "")
for checkpoint_id in assessment.get("day10", {}).get("checkpoint2_required", []):
    require(cp2, f"### {checkpoint_id}", "checkpoint 2")
forbid(cp2, "01-16", "checkpoint 2 core")

bonus_marker = "## Необязательный бонус 10F"
require(final_exam, bonus_marker, "final exam")
core_exam, _, bonus = final_exam.partition(bonus_marker)
forbid(core_exam, "01-16", "final exam core")
require(bonus, "01-16", "final exam bonus")

# Checkpoint task/key identity and machine-readable assessment contract.
cp_sections = level2_sections(checkpoints, "Контрольная точка ")
key_sections = level2_sections(checkpoint_keys, "Контрольная точка ")
for number_text, contract in assessment.get("checkpoints", {}).items():
    number = int(number_text)
    cp = cp_sections.get(number, "")
    key = key_sections.get(number, "")
    if not cp or not key:
        errors.append(f"missing checkpoint/key section {number}")
        continue
    task_ids = heading_ids(cp, f"CP{number}-")
    key_ids = heading_ids(key, f"CP{number}-")
    if task_ids != key_ids:
        errors.append(f"checkpoint {number} IDs differ: tasks={task_ids}, keys={key_ids}")
    scoring = (
        f"**Максимум:** {contract['maximum']}. **Проход:** {contract['threshold']}. "
        f"**Критические задания:** "
    )
    require(cp, scoring, f"checkpoint {number}")
    require(key, scoring, f"checkpoint key {number}")
    for critical in contract["critical"]:
        if critical not in task_ids:
            errors.append(f"checkpoint {number} critical ID is absent: {critical}")
    require(cp, "**Минимумы по измерениям:**", f"checkpoint {number}")
    require(key, "**Минимумы по измерениям:**", f"checkpoint key {number}")
    if contract["maximum"] != 2 * len(task_ids):
        errors.append(f"checkpoint {number} maximum does not match task count")

# Final exam must enforce both total and block minima and keep answers separate.
for marker in ("<details", "<summary>", "Ожидаемый фрагмент"):
    forbid(final_exam, marker, "final_exam")
final_contract = assessment.get("final_exam", {})
require(final_exam, f"Максимум: {final_contract.get('maximum')} баллов", "final_exam")
require(final_exam, f"Общий проход: не менее {final_contract.get('threshold')}", "final_exam")
for block, minimum in final_contract.get("block_minimums", {}).items():
    require(final_exam, f"{block}≥{minimum}", "final_exam")
for critical in final_contract.get("critical", []):
    require(final_exam, critical, "final_exam")
require(final_keys, "total >= 80", "final_exam_keys")
require(final_keys, "A >= 12", "final_exam_keys")
require(final_keys, "E >= 9", "final_exam_keys")

# Day 25 is a route, not ten chapters hidden under one day.
word_count = len(re.findall(r"[A-Za-zА-Яа-яЁё0-9_]+", day25))
if word_count > 2500:
    errors.append(f"day_25 is overloaded: {word_count} words")
for link in ("/final_exam", "/final_exam_keys", "/final_remediation"):
    require(day25, link, "day_25")

# Navigation exposes recovery and final-assessment surfaces.
config = read("docs/.vitepress/config.mts")
for link in (
    "/prerequisite_refreshers",
    "/transfer_walkthroughs",
    "/final_exam",
    "/final_exam_keys",
    "/final_remediation",
):
    require(config, f'link: "{link}"', "VitePress navigation")

# Environment support must not imply verification that CI does not perform.
support = read("docs/support_matrix.md")
require(support, "CI-verified", "support_matrix")
require(support, "documented, manually unverified", "support_matrix")
forbid(support, "Fedora x86-64 | поддерживается", "support_matrix")
forbid(support, "32-битной набор", "support_matrix")

# AI repeated-failure scenarios must be actual multi-turn fixtures.
ai_eval = read("docs/ai_tutor_eval.md")
require(ai_eval, "массив последовательных ходов", "ai_tutor_eval")
try:
    cases = json.loads(read("evals/ai_tutor_cases.json"))
except json.JSONDecodeError as exc:
    errors.append(f"invalid AI tutor cases: {exc}")
else:
    if cases.get("provider_status") != "NOT_RUN":
        errors.append("AI tutor provider status must remain NOT_RUN")
    by_id = {case.get("id"): case for case in cases.get("cases", [])}
    for case_id, minimum_turns in (("AI-05-recovery-switch", 3), ("AI-06-third-failure-prerequisite", 4)):
        turns = by_id.get(case_id, {}).get("turns")
        if not isinstance(turns, list) or len(turns) < minimum_turns:
            errors.append(f"{case_id} lacks a real multi-turn fixture")

# Known mechanical-translation regressions.
banned_phrases = (
    "знаковая/беззнаковая интерпретация интерпретацию",
    "В построчное расположение",
    "Возможный расположение",
    "переход к следующему узлу связный список",
    "стартовый код-код",
    "address return",
)
for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for phrase in banned_phrases:
        if phrase in text:
            errors.append(f"mechanical-translation phrase {phrase!r}: {path.relative_to(ROOT)}")

if errors:
    print("Pedagogical validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Pedagogical validation passed")
