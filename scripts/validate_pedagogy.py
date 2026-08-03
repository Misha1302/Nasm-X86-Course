#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

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


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def forbid(text: str, marker: str, owner: str) -> None:
    if marker in text:
        errors.append(f"{owner} contains forbidden marker {marker!r}")


def heading_ids(text: str, prefix: str) -> list[str]:
    return re.findall(rf"(?m)^### ({re.escape(prefix)}[A-Z0-9-]+)\b", text)


def normalize(text: str) -> str:
    text = text.lower().replace("dword ptr", "dword").replace("word ptr", "word").replace("byte ptr", "byte")
    return re.sub(r"[^a-z0-9_+%\[\]=<>!*/-]+", "", text)


try:
    assessment = json.loads(read("scripts/assessment_contract.json"))
except json.JSONDecodeError as exc:
    errors.append(f"invalid assessment contract: {exc}")
    assessment = {}

require(assessment.get("schema_version") == "2.0", "pedagogy validator requires assessment schema 2.0")
require(assessment.get("canonical_owner") == "scripts/assessment_contract.json", "assessment owner drifted")

required_sources = {
    "docs/prerequisite_refreshers.md",
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
    require(f"<!-- source: {source} -->" in textbook, f"generated textbook lacks source {source}")

closed = read("docs/closed_book_workbook.md")
for marker in ("<details", "</details>", "<summary>"):
    forbid(closed.lower(), marker, "closed_book_workbook")
require("<!-- source-final-exam: docs/final_exam.md -->" in closed, "closed_book_workbook lacks final exam source marker")
try:
    fingerprints = json.loads(read("scripts/answer_fingerprints.json"))
except json.JSONDecodeError as exc:
    errors.append(f"invalid answer fingerprint contract: {exc}")
else:
    closed_norm = normalize(closed)
    for item in fingerprints.get("fingerprints", []):
        targets = item.get("protected_targets", fingerprints.get("protected_targets", []))
        if "docs/closed_book_workbook.md" not in targets:
            continue
        fragment = normalize(item.get("fragment", ""))
        if fragment and fragment in closed_norm:
            errors.append(f"closed-book fingerprint leak: {item.get('id')}")

# The admission page is deliberately answer-free; exact answers live only in keys/examples.
day25 = read("docs/day_25.md")
final_exam = read("docs/final_exam.md")
final_keys = read("docs/final_exam_keys.md")
instruction_reference = read("docs/instruction_reference.md")
example_sum = read("examples/09_aligned_sum_call.asm")
correct_sum_call = "sub esp, 8\npush dword [b]\npush dword [a]\ncall sum\nadd esp, 16"
forbid(day25, correct_sum_call, "day_25")
require(correct_sum_call in final_keys, "final_exam_keys lacks canonical aligned sum answer")
for marker in ("sub esp, 8", "call sum", "add esp, 16"):
    require(marker in example_sum, f"aligned sum example lacks {marker!r}")
for route in ("/final_exam", "/final_exam_keys", "/final_remediation"):
    require(route in day25, f"day_25 lacks route {route}")
require("CP1 + CP2 + CP3 + CP4 + CP5 + CP6 + FINAL" in day25, "day_25 lacks composed readiness contract")
require(re.search(r"```(?:asm|nasm)\b", day25, flags=re.I) is None, "day_25 exposes an ASM answer listing")
if len(re.findall(r"[A-Za-zА-Яа-яЁё0-9_]+", day25)) > 1800:
    errors.append("day_25 is overloaded")

for marker in (
    "fsubp st1,st0` | `st(1)=st(1)-st(0)`",
    "fdivp st1,st0` | `st(1)=st(1)/st(0)`",
):
    require(marker in instruction_reference, f"instruction_reference lacks exact x87 direction {marker!r}")

checkpoints = read("docs/checkpoints.md")
checkpoint_keys = read("docs/checkpoint_keys.md")
for aid in [f"CP{i}" for i in range(1, 7)]:
    contract = assessment.get("assessments", {}).get(aid, {})
    tasks = list(contract.get("tasks", {}))
    task_ids = heading_ids(checkpoints, aid + "-")
    key_ids = heading_ids(checkpoint_keys, aid + "-")
    require(task_ids == tasks, f"{aid} task order differs from canonical contract: {task_ids} != {tasks}")
    require(key_ids == tasks, f"{aid} key order differs from canonical contract: {key_ids} != {tasks}")
    maximum = contract.get("maximum")
    threshold = contract.get("threshold")
    scoring = f"**Максимум:** {maximum}. **Проход:** {threshold}. **Критические задания:**"
    require(scoring in checkpoints, f"{aid} scoring prose is not synchronized")
    require(scoring in checkpoint_keys, f"{aid} key scoring prose is not synchronized")
    for rule in contract.get("critical_task_rules", []):
        require(rule.get("task") in tasks, f"{aid} critical rule references unknown task {rule.get('task')}")

# Day 10 core/bonus routing is sourced from the canonical contract.
day10 = assessment.get("day10", {})
require(day10.get("mandatory_sessions") == ["10A", "10B", "10C", "10D", "10E"], "mandatory Day 10 sessions drifted")
require(day10.get("optional_sessions") == ["10F"], "10F is not optional")
cp2_tasks = assessment.get("assessments", {}).get("CP2", {}).get("tasks", {})
for required_task in day10.get("checkpoint2_required", []):
    require(required_task in cp2_tasks, f"Day 10 required evidence task missing from CP2: {required_task}")
require("CP2-IDIV-OVERFLOW" in cp2_tasks, "signed division overflow lacks separate CP2 evidence")

bonus_marker = "## Необязательный бонус 10F"
require(bonus_marker in final_exam, "final exam lacks an explicit 10F bonus section")
_, _, bonus = final_exam.partition(bonus_marker)
require("01-16" in bonus, "01-16 is absent from the bonus section")
require("bonus-only" in final_exam, "final exam does not state that 10F/01-16 are bonus-only")

final_contract = assessment.get("assessments", {}).get("FINAL", {})
require(f"Максимум: {final_contract.get('maximum')} баллов" in final_exam, "final_exam maximum is not synchronized")
require(f"Общий проход: не менее {final_contract.get('threshold')}" in final_exam, "final_exam threshold is not synchronized")
for block, data in final_contract.get("block_minimums", {}).items():
    require(f"{block}≥{data.get('minimum')}" in final_exam, f"final_exam lacks {block} block minimum")
for rule in final_contract.get("critical_task_rules", []):
    require(rule.get("task") in final_exam, f"final_exam lacks critical task {rule.get('task')}")
for marker in ("<details", "<summary>", "Ожидаемый фрагмент"):
    forbid(final_exam, marker, "final_exam")
require("total >= 80" in final_keys, "final_exam_keys lacks total predicate")
require("A >= 12" in final_keys and "E >= 9" in final_keys, "final_exam_keys lacks block predicates")

config = read("docs/.vitepress/config.mts")
for link in (
    "/prerequisite_refreshers",
    "/transfer_walkthroughs",
    "/final_exam",
    "/final_exam_keys",
    "/final_remediation",
):
    require(f'link: "{link}"' in config, f"VitePress navigation lacks {link}")

support = read("docs/support_matrix.md")
require("CI-verified" in support, "support_matrix lacks CI-verified status")
require("documented, manually unverified" in support, "support_matrix lacks explicit unverified status")
forbid(support, "Fedora x86-64 | поддерживается", "support_matrix")
forbid(support, "32-битной набор", "support_matrix")

ai_eval = read("docs/ai_tutor_eval.md")
require("массив последовательных ходов" in ai_eval, "ai_tutor_eval lacks multi-turn fixture contract")
try:
    cases = json.loads(read("evals/ai_tutor_cases.json"))
except json.JSONDecodeError as exc:
    errors.append(f"invalid AI tutor cases: {exc}")
else:
    require(cases.get("provider_status") == "NOT_RUN", "AI provider status must remain NOT_RUN")
    by_id = {case.get("id"): case for case in cases.get("cases", [])}
    for case_id, minimum_turns in (("AI-05-recovery-switch", 3), ("AI-06-third-failure-prerequisite", 4)):
        turns = by_id.get(case_id, {}).get("turns")
        require(isinstance(turns, list) and len(turns) >= minimum_turns, f"{case_id} lacks a real multi-turn fixture")

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
