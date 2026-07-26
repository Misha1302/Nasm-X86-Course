#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
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
            family = fence_match.group(1)[0]
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


def slugify_heading(title: str) -> str:
    title = re.sub(r"`([^`]*)`", r"\1", title)
    title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title)
    title = re.sub(r"<[^>]+>", "", title)
    title = title.strip().lower()
    title = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    title = re.sub(r"[\s_-]+", "-", title).strip("-")
    return title


def resolve_doc_path(path_part: str) -> Path | None:
    if path_part == "/":
        return DOCS / "index.md"
    relative = path_part.removeprefix("/").rstrip("/")
    direct = DOCS / f"{relative}.md"
    index = DOCS / relative / "index.md"
    if direct.is_file():
        return direct
    if index.is_file():
        return index
    return None


def anchors_for(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+id=["\']([^"\']+)["\']\s*></a>', text, flags=re.I))
    counts: dict[str, int] = {}
    for heading in headings_outside_fences(text):
        base = slugify_heading(heading.title)
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def validate_doc_link(target: str, source: Path) -> None:
    path_part, sep, anchor = target.partition("#")
    target_path = resolve_doc_path(path_part)
    if target_path is None:
        errors.append(f"broken Markdown link {target!r}: {source.relative_to(ROOT)}")
        return
    if sep and anchor and anchor not in anchors_for(target_path):
        errors.append(
            f"broken Markdown anchor {anchor!r} in {target!r}: {source.relative_to(ROOT)}"
        )


def require_markers(rel: str, markers: tuple[str, ...]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing required file: {rel}")
        return
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"missing marker {marker!r} in {rel}")


def ids_from_headings(text: str, pattern: str, level: int) -> list[str]:
    ids: list[str] = []
    regex = re.compile(pattern)
    for heading in headings_outside_fences(text):
        if heading.level != level:
            continue
        match = regex.match(heading.title)
        if match:
            ids.append(match.group(1))
    return ids


# Core day files and chapter structure.
required_day_headings = (
    "Входные знания",
    "За 30 секунд",
    "Минимум после главы",
    "Практика",
    "Чеклист",
    "Следующий шаг",
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
    checklist_items = re.findall(r"(?m)^\s*- \[ \] .+$", checklist)
    if len(checklist_items) < 3:
        errors.append(f"checklist has fewer than three observable actions: {path.relative_to(ROOT)}")
    for item in checklist_items:
        if re.search(r"\bпонимать\b", item, flags=re.I):
            errors.append(f"checklist uses non-observable verb 'понимать': {path.relative_to(ROOT)}: {item.strip()}")

    next_step = section_text(text, headings, "Следующий шаг")
    expected_workbook = f"](/transfer_workbook#tr-{day:02d})"
    expected_key = f"](/transfer_keys#key-tr-{day:02d})"
    if expected_workbook not in next_step or expected_key not in next_step:
        errors.append(f"next-step section lacks exact TR-{day:02d} task/key links: {path.relative_to(ROOT)}")

    error_heading_markers = ("Типовые ошибки", "Частые ошибки", "Что может пойти не так", "типовых провалов")
    if not any(any(marker.lower() in heading.title.lower() for marker in error_heading_markers) for heading in headings):
        errors.append(f"missing a real typical-errors section: {path.relative_to(ROOT)}")
    if "```" not in text:
        errors.append(f"chapter has no executable/diagram example: {path.relative_to(ROOT)}")


# Transfer task/key identity and diagnostic contracts.
workbook_path = DOCS / "transfer_workbook.md"
keys_path = DOCS / "transfer_keys.md"
workbook = workbook_path.read_text(encoding="utf-8")
keys = keys_path.read_text(encoding="utf-8")
expected_transfer_ids = [f"TR-{day:02d}" for day in range(1, 26)]
workbook_ids = ids_from_headings(workbook, r"(TR-\d{2})\b", 2)
key_ids = ids_from_headings(keys, r"(TR-\d{2})\b", 2)
if workbook_ids != expected_transfer_ids:
    errors.append(f"transfer workbook IDs mismatch: {workbook_ids}")
if key_ids != expected_transfer_ids:
    errors.append(f"transfer key IDs mismatch: {key_ids}")
if workbook_ids != key_ids:
    errors.append("transfer task IDs and key IDs are not mirrored")
for transfer_id in expected_transfer_ids:
    key_section = section_text(keys, headings_outside_fences(keys), transfer_id)
    for marker in ("Инвариант", "Типовая ошибка", "Контрпример", "Повторение"):
        if marker not in key_section:
            errors.append(f"{transfer_id} key lacks diagnostic marker {marker!r}")


# Checkpoint identity, scoring and mirror validation.
checkpoints_path = DOCS / "checkpoints.md"
checkpoint_keys_path = DOCS / "checkpoint_keys.md"
checkpoints = checkpoints_path.read_text(encoding="utf-8")
checkpoint_keys = checkpoint_keys_path.read_text(encoding="utf-8")
checkpoint_headings = [
    h for h in headings_outside_fences(checkpoints)
    if h.level == 2 and h.title.startswith("Checkpoint ")
]
key_checkpoint_headings = [
    h for h in headings_outside_fences(checkpoint_keys)
    if h.level == 2 and h.title.startswith("Checkpoint ")
]
if len(checkpoint_headings) != 6:
    errors.append(f"expected six checkpoints, found {len(checkpoint_headings)}")
if len(key_checkpoint_headings) != 6:
    errors.append(f"expected six checkpoint key sections, found {len(key_checkpoint_headings)}")

for number in range(1, 7):
    cp_heading = next((h for h in checkpoint_headings if h.title.startswith(f"Checkpoint {number} ")), None)
    key_heading = next((h for h in key_checkpoint_headings if h.title == f"Checkpoint {number}"), None)
    if cp_heading is None or key_heading is None:
        continue
    cp_section = section_text(checkpoints, headings_outside_fences(checkpoints), cp_heading.title)
    key_section = section_text(checkpoint_keys, headings_outside_fences(checkpoint_keys), key_heading.title)
    cp_ids = ids_from_headings(cp_section, rf"(CP{number}-[A-Z0-9-]+)\b", 3)
    key_ids_for_cp = ids_from_headings(key_section, rf"(CP{number}-[A-Z0-9-]+)\b", 3)
    if cp_ids != key_ids_for_cp:
        errors.append(f"checkpoint {number} IDs are not mirrored: tasks={cp_ids}, keys={key_ids_for_cp}")

    score_match = re.search(
        r"\*\*Максимум:\*\*\s*(\d+)\.\s*\*\*Проход:\*\*\s*(\d+)\.\s*\*\*Критические ID:\*\*\s*([^\n]+)",
        cp_section,
    )
    key_score_match = re.search(
        r"\*\*Максимум:\*\*\s*(\d+)\.\s*\*\*Проход:\*\*\s*(\d+)\.\s*\*\*Критические ID:\*\*\s*([^\n]+)",
        key_section,
    )
    if score_match is None or key_score_match is None:
        errors.append(f"checkpoint {number} lacks parseable scoring contract in task or key")
        continue
    maximum, threshold = int(score_match.group(1)), int(score_match.group(2))
    key_maximum, key_threshold = int(key_score_match.group(1)), int(key_score_match.group(2))
    if (maximum, threshold) != (key_maximum, key_threshold):
        errors.append(f"checkpoint {number} scoring differs between task and key")
    if maximum != len(cp_ids) * 2:
        errors.append(f"checkpoint {number} maximum {maximum} does not equal 2 × {len(cp_ids)} tasks")
    if threshold * 100 < maximum * 80:
        errors.append(f"checkpoint {number} threshold is below 80%: {threshold}/{maximum}")
    critical_ids = re.findall(r"`(CP\d-[A-Z0-9-]+)`", score_match.group(3))
    if not critical_ids or any(item not in cp_ids for item in critical_ids):
        errors.append(f"checkpoint {number} has invalid critical IDs: {critical_ids}")

    for checkpoint_id in cp_ids:
        key_item = section_text(checkpoint_keys, headings_outside_fences(checkpoint_keys), checkpoint_id)
        for marker in ("Инвариант", "Типовая ошибка", "Контрпример", "Повторение", "Вариант"):
            if marker not in key_item:
                errors.append(f"{checkpoint_id} key lacks marker {marker!r}")

checkpoint1_title = next(h.title for h in checkpoint_headings if h.title.startswith("Checkpoint 1 "))
checkpoint1 = section_text(checkpoints, headings_outside_fences(checkpoints), checkpoint1_title)
for forbidden in ("movzx", "movsx", "scanf", "printf", "idiv", "cdq"):
    if forbidden.lower() in checkpoint1.lower():
        errors.append(f"checkpoint 1 leaks post-Day-04 material: {forbidden!r}")


# Standalone-learning pages and AI tutor contract.
standalone_pages = {
    "docs/self_study.md": (
        "Цикл одной главы",
        "Интервальное повторение",
        "Журнал ошибок",
        "](/transfer_workbook)",
        "](/checkpoint_keys)",
        "](/ai_tutor_prompts)",
    ),
    "docs/day_10_learning_path.md": tuple(f"Сессия 10{letter}" for letter in "ABCDE"),
    "docs/ai_tutor_prompts.md": (
        "<task>",
        "<chapter>",
        "<answer>",
        "Вторая ошибка",
        "Третья ошибка",
        "непроверенной",
        "](/ai_tutor_eval)",
    ),
    "docs/ai_tutor_eval.md": (
        "Live DeepSeek run",
        "не сохранён",
        "STRUCTURALLY_VALID",
        "BEHAVIORALLY_VERIFIED",
    ),
}
for rel, markers in standalone_pages.items():
    require_markers(rel, markers)

cases_path = ROOT / "evals" / "ai_tutor_cases.json"
if not cases_path.is_file():
    errors.append("missing evals/ai_tutor_cases.json")
else:
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid AI tutor eval JSON: {exc}")
    else:
        items = cases.get("cases")
        if cases.get("provider_status") != "NOT_RUN":
            errors.append("AI tutor provider status must remain NOT_RUN until provenance-bearing live results exist")
        if not isinstance(items, list) or len(items) < 10:
            errors.append("AI tutor eval must contain at least 10 behavioral cases")
        else:
            ids = [item.get("id") for item in items]
            if len(ids) != len(set(ids)):
                errors.append("AI tutor eval case IDs must be unique")
            for item in items:
                if not item.get("must") or not item.get("must_not"):
                    errors.append(f"AI tutor eval case lacks must/must_not contract: {item.get('id')}")


# Generated documents.
for generated in (DOCS / "textbook.md", DOCS / "course_migration.md"):
    if not generated.is_file() or "сгенерирован" not in generated.read_text(encoding="utf-8").lower():
        errors.append(f"generated document is absent or lacks marker: {generated.relative_to(ROOT)}")

textbook = DOCS / "textbook.md"
if textbook.is_file():
    textbook_text = textbook.read_text(encoding="utf-8")
    for source in (
        "docs/self_study.md",
        "docs/day_01.md",
        "docs/day_25.md",
        "docs/day_10_learning_path.md",
        "docs/transfer_workbook.md",
        "docs/transfer_keys.md",
        "docs/checkpoints.md",
        "docs/checkpoint_keys.md",
        "docs/ai_tutor_prompts.md",
        "docs/ai_tutor_eval.md",
    ):
        if f"<!-- source: {source} -->" not in textbook_text:
            errors.append(f"generated textbook lacks source {source}")

migration = DOCS / "course_migration.md"
if migration.is_file():
    rows = [line for line in migration.read_text(encoding="utf-8").splitlines() if re.match(r"^\| \[Day \d{2}\]", line)]
    if len(rows) != 25 or any("| standalone | 6/6 |" not in row for row in rows):
        errors.append("generated standalone status must contain 25 standalone 6/6 rows")


# Existing support pages and duplicate ownership.
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
if (DOCS / "fpu_double_site_page.md").exists():
    errors.append("duplicate owner docs/fpu_double_site_page.md must not exist")
popular = DOCS / "popular_instructions.md"
if popular.is_file():
    popular_text = popular.read_text(encoding="utf-8")
    if "](/instruction_reference)" not in popular_text:
        errors.append("popular_instructions.md must delegate to canonical instruction reference")
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


# Validate root-relative Markdown links and anchors.
for path in DOCS.rglob("*.md"):
    if path.name in {"textbook.md", "course_migration.md"}:
        continue
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\((/[^)]+)\)", text):
        validate_doc_link(target, path)

config = (DOCS / ".vitepress" / "config.mts").read_text(encoding="utf-8")
for link in re.findall(r'link:\s*"(/[^"]+)"', config):
    validate_doc_link(link, DOCS / ".vitepress" / "config.mts")
for required_link in (
    "/self_study",
    "/transfer_workbook",
    "/transfer_keys",
    "/checkpoints",
    "/checkpoint_keys",
    "/ai_tutor_prompts",
    "/ai_tutor_eval",
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
    "docs/ai_tutor_eval.md",
    "шесть",
):
    if marker not in readme:
        errors.append(f"README lacks standalone-course marker {marker!r}")
if "постепенно переводится" in readme:
    errors.append("README still describes chapter migration as ongoing")

if errors:
    raise SystemExit("Course validation failed:\n- " + "\n- ".join(errors))
print("Course validation passed")
