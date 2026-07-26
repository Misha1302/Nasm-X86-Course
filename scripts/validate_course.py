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


# Core day files and real Markdown structure.
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
    practice_subheadings = [
        heading for heading in headings
        if heading.line > next((h.line for h in headings if h.title == "Практика"), 10**9)
        and heading.level >= 3
    ]
    # Restrict to the practice section boundary.
    if practice:
        practice_headings = headings_outside_fences(practice)
        if len([h for h in practice_headings if h.level >= 3]) < 2:
            errors.append(f"practice must contain at least two observable tasks: {path.relative_to(ROOT)}")

    checklist = section_text(text, headings, "Чеклист")
    checklist_items = re.findall(r"(?m)^\s*- \[ \] ", checklist)
    if len(checklist_items) < 3:
        errors.append(f"checklist has fewer than three observable actions: {path.relative_to(ROOT)}")

    error_heading_markers = ("Типовые ошибки", "Частые ошибки", "Что может пойти не так", "типовых провалов")
    if not any(any(marker.lower() in heading.title.lower() for marker in error_heading_markers) for heading in headings):
        errors.append(f"missing a real typical-errors section: {path.relative_to(ROOT)}")

    if "```" not in text:
        errors.append(f"chapter has no executable/diagram example: {path.relative_to(ROOT)}")


# Learning-support pages and generated documents.
for rel in ("docs/checkpoints.md", "docs/instruction_reference.md", "docs/popular_instructions.md"):
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
        errors.append("popular_instructions.md must remain a short compatibility index, not a second reference owner")


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


# Decision-critical technical boundaries and semantic regressions.
required_markers = {
    "docs/day_25.md": ["uint32_t mask = 0u - (ux >> 31);", "INT32_MIN", "**100**", "**90 мин**"],
    "docs/day_10.md": ["может переполниться", "INT32_MIN"],
    "docs/patterns/branchless.md": ["INT32_MIN"],
    "docs/tasks/spring-01/01-14-garden.md": ["может переполниться"],
}
for rel, markers in required_markers.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"missing technical boundary {marker!r} in {rel}")

for path in DOCS.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"(?im)^\s*(?:i?div)\s+(?:[-+]?\d+|0x[0-9a-f]+|[0-9a-f]+h)\b", text):
        line = text.count("\n", 0, match.start()) + 1
        errors.append(f"division instruction cannot use an immediate operand: {path.relative_to(ROOT)}:{line}")

startup_text = (DOCS / "day_20.md").read_text(encoding="utf-8")
if re.search(r"`?main`?\s+вызывает\s+runtime", startup_text, flags=re.I):
    errors.append("day_20.md reverses the startup direction: runtime calls main")

checkpoints = (DOCS / "checkpoints.md").read_text(encoding="utf-8")
checkpoint_headings = [h for h in headings_outside_fences(checkpoints) if h.level == 2 and h.title.startswith("Checkpoint ")]
if len(checkpoint_headings) != 5:
    errors.append(f"expected five checkpoints, found {len(checkpoint_headings)}")
for number in range(1, 6):
    heading = next((h for h in checkpoint_headings if h.title.startswith(f"Checkpoint {number} ")), None)
    if heading is None:
        continue
    section = section_text(checkpoints, headings_outside_fences(checkpoints), heading.title)
    for label in ("**Trace.", "**Пропуски.", "**Напиши.", "**Найди баг."):
        if label not in section:
            errors.append(f"checkpoint {number} lacks mode {label}")
    if "___" not in section:
        errors.append(f"checkpoint {number} has no literal fill-in-the-blank markers")

coverage_markers = {
    3: ("jump table", ".table"),
    4: ("struct Node", "reverse"),
    5: ("0.1", "NaN", "return address"),
}
checkpoint_sections = headings_outside_fences(checkpoints)
for number, markers in coverage_markers.items():
    title = next(h.title for h in checkpoint_sections if h.level == 2 and h.title.startswith(f"Checkpoint {number} "))
    section = section_text(checkpoints, checkpoint_sections, title)
    for marker in markers:
        if marker.lower() not in section.lower():
            errors.append(f"checkpoint {number} claims coverage but lacks marker {marker!r}")

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


# Validate all root-relative Markdown links, not only VitePress navigation.
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
if 'text: "Checkpoints"' in config:
    errors.append("Russian navigation must use 'Контрольные точки', not 'Checkpoints'")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
if "постепенно переводится" in readme:
    errors.append("README still describes the completed chapter migration as ongoing")

if errors:
    raise SystemExit("Course validation failed:\n- " + "\n- ".join(errors))
print("Course validation passed")
