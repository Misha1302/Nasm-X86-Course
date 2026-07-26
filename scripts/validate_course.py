#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
errors: list[str] = []


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    line: int


def headings_outside_fences(text: str) -> list[Heading]:
    headings: list[Heading] = []
    fence: str | None = None
    for line_number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.lstrip()
        fence_match = re.match(r"(```+|~~~+)", stripped)
        if fence_match:
            token = fence_match.group(1)
            family = token[0]
            if fence is None:
                fence = family
            elif fence == family:
                fence = None
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", raw)
        if match:
            headings.append(Heading(len(match.group(1)), match.group(2).strip(), line_number))
    return headings


def section_text(text: str, headings: list[Heading], title: str) -> str:
    matches = [heading for heading in headings if heading.title == title]
    if len(matches) != 1:
        return ""
    start = matches[0]
    lines = text.splitlines()
    end_line = len(lines) + 1
    for heading in headings:
        if heading.line > start.line and heading.level <= start.level:
            end_line = heading.line
            break
    return "\n".join(lines[start.line:end_line - 1])


def resolve_doc_link(target: str) -> bool:
    path_part = target.split("#", 1)[0]
    if path_part == "/":
        return True
    relative = path_part.removeprefix("/").rstrip("/")
    return (DOCS / f"{relative}.md").is_file() or (DOCS / relative / "index.md").is_file()


def require_markers(rel: str, markers: tuple[str, ...]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing required file: {rel}")
        return
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"missing marker {marker!r} in {rel}")


# Core day files and chapter structure.
required_day_headings = (
    "Входные знания",
    "За 30 секунд",
    "Минимум после главы",
    "Практика",
    "Чеклист",
)
for day in range(1, 26):
    path = DOCS / f"day_{day:02d}.md"
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")
        continue

    text = path.read_text(encoding="utf-8")
    headings = headings_outside_fences(text)
    level2 = [heading for heading in headings if heading.level == 2]
    positions: list[int] = []
    for title in required_day_headings:
        matches = [heading for heading in level2 if heading.title == title]
        if len(matches) != 1:
            errors.append(
                f"expected exactly one real level-2 heading {title!r}: "
                f"{path.relative_to(ROOT)} (found {len(matches)})"
            )
            positions.append(-1)
        else:
            positions.append(matches[0].line)
    if all(position >= 0 for position in positions) and positions != sorted(positions):
        errors.append(f"pedagogical headings are out of order: {path.relative_to(ROOT)}")

    prerequisite = section_text(text, headings, "Входные знания")
    if day > 1 and not re.search(r"\]\(/(?:day_\d{2}|checkpoints|support_matrix)(?:#[^)]+)?\)", prerequisite):
        errors.append(f"prerequisite section lacks a concrete clickable return route: {path.relative_to(ROOT)}")

    practice = section_text(text, headings, "Практика")
    if practice:
        practice_headings = headings_outside_fences(practice)
        if len([h for h in practice_headings if h.level >= 3]) < 2:
            errors.append(f"practice must contain at least two observable tasks: {path.relative_to(ROOT)}")

    checklist = section_text(text, headings, "Чеклист")
    if len(re.findall(r"(?m)^\s*- \[ \] ", checklist)) < 3:
        errors.append(f"checklist has fewer than three observable actions: {path.relative_to(ROOT)}")

    error_heading_markers = ("Типовые ошибки", "Частые ошибки", "Что может пойти не так", "типовых провалов")
    if not any(any(marker.lower() in heading.title.lower() for marker in error_heading_markers) for heading in headings):
        errors.append(f"missing a real typical-errors section: {path.relative_to(ROOT)}")
    if "```" not in text:
        errors.append(f"chapter has no executable/diagram example: {path.relative_to(ROOT)}")


# Standalone-learning surface.
standalone_pages = {
    "docs/self_study.md": (
        "Цикл одной главы",
        "Интервальное повторение",
        "Журнал ошибок",
        "](/transfer_workbook)",
        "](/checkpoint_keys)",
        "](/ai_tutor_prompts)",
    ),
    "docs/transfer_workbook.md": tuple(f"## День {day:02d}" for day in range(1, 26)),
    "docs/transfer_keys.md": tuple(f"## День {day:02d}" for day in range(1, 26)),
    "docs/checkpoint_keys.md": tuple(f"## Checkpoint {number}" for number in range(1, 7)),
    "docs/ai_tutor_prompts.md": (
        "Универсальный наставник по главе",
        "Совместное изучение новой темы",
        "Режим строгого зачёта",
        "Диагностика непонимания",
        "Разбор моего решения",
        "Устный тренажёр",
        "DeepSeek",
    ),
    "docs/day_10_learning_path.md": tuple(f"Сессия 10{letter}" for letter in "ABCDE"),
    "docs/checkpoints.md": tuple(f"Checkpoint {number}" for number in range(1, 7)),
}
for rel, markers in standalone_pages.items():
    require_markers(rel, markers)

self_study = (DOCS / "self_study.md").read_text(encoding="utf-8")
for phrase in ("не является результатом", "Центральные инварианты", "На следующий день", "Через 7 дней"):
    if phrase not in self_study:
        errors.append(f"self-study contract lacks {phrase!r}")

workbook = (DOCS / "transfer_workbook.md").read_text(encoding="utf-8")
keys = (DOCS / "transfer_keys.md").read_text(encoding="utf-8")
if len(re.findall(r"(?m)^## День \d{2}", workbook)) != 25:
    errors.append("transfer workbook must contain exactly 25 day tasks")
if len(re.findall(r"(?m)^## День \d{2}", keys)) != 25:
    errors.append("transfer keys must contain exactly 25 day keys")
if "](/transfer_keys)" not in workbook:
    errors.append("transfer workbook must link to separate keys")

prompts = (DOCS / "ai_tutor_prompts.md").read_text(encoding="utf-8")
for invariant in (
    "не показывай решение",
    "по одному",
    "IA-32",
    "не смешивай IA-32 и x86-64",
    "нарушенный инвариант",
):
    if invariant.lower() not in prompts.lower():
        errors.append(f"AI tutor pack lacks safety/teaching invariant {invariant!r}")


# Checkpoints: six gates, separate skills, transfer, and corrected Day-04 boundary.
checkpoints = (DOCS / "checkpoints.md").read_text(encoding="utf-8")
checkpoint_headings = [
    h for h in headings_outside_fences(checkpoints)
    if h.level == 2 and h.title.startswith("Checkpoint ")
]
if len(checkpoint_headings) != 6:
    errors.append(f"expected six checkpoints, found {len(checkpoint_headings)}")
for number in range(1, 7):
    heading = next((h for h in checkpoint_headings if h.title.startswith(f"Checkpoint {number} ")), None)
    if heading is None:
        continue
    section = section_text(checkpoints, headings_outside_fences(checkpoints), heading.title)
    for mode in ("Trace", "Пропуски", "Напиши", "Найди баг", "Transfer"):
        if mode not in section:
            errors.append(f"checkpoint {number} lacks mode {mode!r}")
    if "Критические навыки" not in section:
        errors.append(f"checkpoint {number} lacks critical-skill declaration")

checkpoint1 = section_text(checkpoints, headings_outside_fences(checkpoints), checkpoint_headings[0].title)
for forbidden in ("mov [a], [b]", "push x", "printf", "scanf"):
    if forbidden in checkpoint1:
        errors.append(f"checkpoint 1 leaks post-Day-04 material: {forbidden!r}")
for required in ("signed", "unsigned", "размер", "ah", "al"):
    if required.lower() not in checkpoint1.lower():
        errors.append(f"checkpoint 1 lacks Day-04 skill {required!r}")

coverage_markers = {
    2: ("edx:eax", "маск", "округление"),
    3: ("jump table", "флаг", "адрес"),
    4: ("return address", "Node", "callee-saved"),
    5: ("0.1", "x87", "qword", "startup", "NaN"),
    6: ("hidden `this`", "vptr", "indirect"),
}
for number, markers in coverage_markers.items():
    title = next(h.title for h in checkpoint_headings if h.title.startswith(f"Checkpoint {number} "))
    section = section_text(checkpoints, headings_outside_fences(checkpoints), title)
    for marker in markers:
        if marker.lower() not in section.lower():
            errors.append(f"checkpoint {number} claims coverage but lacks marker {marker!r}")


# Existing support pages and generated documents.
for rel in (
    "docs/instruction_reference.md",
    "docs/popular_instructions.md",
    "docs/how_to_solve_tasks.md",
    "docs/debug_cards.md",
    "docs/debugging_with_gdb.md",
    "docs/support_matrix.md",
):
    if not (ROOT / rel).is_file():
        errors.append(f"missing learning support page: {rel}")

for generated in (DOCS / "textbook.md", DOCS / "course_migration.md"):
    if not generated.is_file() or "сгенерирован" not in generated.read_text(encoding="utf-8").lower():
        errors.append(f"generated document is absent or lacks marker: {generated.relative_to(ROOT)}")

migration = DOCS / "course_migration.md"
if migration.is_file():
    rows = [line for line in migration.read_text(encoding="utf-8").splitlines() if re.match(r"^\| \[Day \d{2}\]", line)]
    if len(rows) != 25 or any("| structured | 5/5 |" not in row for row in rows):
        errors.append("generated structure status must contain 25 structured 5/5 rows")

if (DOCS / "fpu_double_site_page.md").exists():
    errors.append("duplicate owner docs/fpu_double_site_page.md must not exist")

popular = DOCS / "popular_instructions.md"
if popular.is_file():
    popular_text = popular.read_text(encoding="utf-8")
    if "](/instruction_reference)" not in popular_text:
        errors.append("popular_instructions.md must delegate to the canonical instruction reference")
    if len(popular_text.splitlines()) > 30 or "```" in popular_text:
        errors.append("popular_instructions.md must remain a short compatibility index")


# Reproducibility and executable examples.
lock = (ROOT / "package-lock.json").read_text(encoding="utf-8")
if "applied-caas-gateway" in lock or "internal.api.openai.org" in lock:
    errors.append("package-lock.json contains a private registry URL")

asm_stems = {path.stem for path in (ROOT / "examples").glob("*.asm")}
expected_stems = {path.stem for path in (ROOT / "examples" / "expected").glob("*.txt")}
if asm_stems != expected_stems:
    errors.append(f"example/expected mismatch: asm={sorted(asm_stems)}, expected={sorted(expected_stems)}")
for path in (ROOT / "examples").glob("*.asm"):
    if ".note.GNU-stack" not in path.read_text(encoding="utf-8"):
        errors.append(f"missing non-executable-stack marker: {path.relative_to(ROOT)}")


# Decision-critical technical boundaries.
required_markers = {
    "docs/day_25.md": ("uint32_t mask = 0u - (ux >> 31);", "INT32_MIN", "**100**", "**90 мин**"),
    "docs/day_10.md": ("может переполниться", "INT32_MIN"),
    "docs/patterns/branchless.md": ("INT32_MIN",),
    "docs/tasks/spring-01/01-14-garden.md": ("может переполниться",),
}
for rel, markers in required_markers.items():
    require_markers(rel, markers)

for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"(?im)^\s*(?:i?div)\s+(?:[-+]?\d+|0x[0-9a-f]+|[0-9a-f]+h)\b", text):
        line = text.count("\n", 0, match.start()) + 1
        errors.append(f"division instruction cannot use an immediate operand: {path.relative_to(ROOT)}:{line}")

startup_text = (DOCS / "day_20.md").read_text(encoding="utf-8")
if re.search(r"`?main`?\s+вызывает\s+runtime", startup_text, flags=re.I):
    errors.append("day_20.md reverses the startup direction: runtime calls main")


day25 = (DOCS / "day_25.md").read_text(encoding="utf-8")
reverse_section_match = re.search(r"### Часть D\. Reverse engineering(.*?)---\n\n### Часть E", day25, flags=re.S)
if reverse_section_match is None:
    errors.append("day_25.md lacks a bounded reverse-engineering section")
else:
    reverse_section = reverse_section_match.group(1)
    if reverse_section.count("push ebp") != 3 or reverse_section.count("pop ebp") != 3:
        errors.append("all three reverse-engineering listings must contain consistent full frames")
score_rows = re.findall(
    r"^\| [A-E]\. .*?\| .*?\| (\d+) \| (\d+) \| (\d+) мин \|$",
    day25,
    flags=re.M,
)
if len(score_rows) != 5:
    errors.append("day_25.md scoring rubric must contain five parseable block rows")
else:
    total_points = sum(int(row[1]) for row in score_rows)
    total_minutes = sum(int(row[2]) for row in score_rows)
    if total_points != 100:
        errors.append(f"day_25.md block points sum to {total_points}, expected 100")
    if total_minutes != 90:
        errors.append(f"day_25.md block times sum to {total_minutes}, expected 90")


# Validate root-relative Markdown links and VitePress navigation.
for path in DOCS.rglob("*.md"):
    if path.name in {"textbook.md", "course_migration.md"}:
        continue
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\((/[^)]+)\)", text):
        if not resolve_doc_link(target):
            errors.append(f"broken Markdown link {target!r}: {path.relative_to(ROOT)}")

config = (DOCS / ".vitepress" / "config.mts").read_text(encoding="utf-8")
for link in re.findall(r'link:\s*"(/[^"]+)"', config):
    if not resolve_doc_link(link):
        errors.append(f"broken sidebar/nav link: {link}")
for required_link in (
    "/self_study",
    "/transfer_workbook",
    "/transfer_keys",
    "/checkpoints",
    "/checkpoint_keys",
    "/ai_tutor_prompts",
    "/day_10_learning_path",
):
    if f'link: "{required_link}"' not in config:
        errors.append(f"VitePress navigation lacks standalone-learning page {required_link}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for marker in (
    "Самостоятельный учебник",
    "docs/self_study.md",
    "docs/transfer_workbook.md",
    "docs/ai_tutor_prompts.md",
    "шесть",
):
    if marker not in readme:
        errors.append(f"README lacks standalone-course marker {marker!r}")
if "постепенно переводится" in readme:
    errors.append("README still describes chapter migration as ongoing")

if errors:
    raise SystemExit("Course validation failed:\n- " + "\n- ".join(errors))
print("Course validation passed")
