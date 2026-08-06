#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GENERATED = {
    "docs/textbook.md",
    "docs/closed_book_workbook.md",
    "docs/course_migration.md",
}


def markdown_sources() -> tuple[Path, ...]:
    result: list[Path] = []
    for path in sorted(DOCS.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        if relative in GENERATED:
            continue
        if any(part.startswith(".") for part in path.relative_to(DOCS).parts):
            continue
        result.append(path)
    return tuple(result)


def visible_heading_slug(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\-\s]", "", text, flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", text).strip("-")


def normalize(text: str, *, relative: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    fence: str | None = None
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    previous_level = 1 if relative == "docs/index.md" else 0
    home_layout = relative == "docs/index.md" and re.search(r"(?m)^layout:\s*home\s*$", text) is not None
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if i == 0 and in_frontmatter:
            output.append(line)
            i += 1
            continue
        if in_frontmatter:
            output.append(line)
            if stripped == "---":
                in_frontmatter = False
            i += 1
            continue

        marker = "```" if stripped.startswith("```") else ("~~~" if stripped.startswith("~~~") else None)
        if marker is not None:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            output.append(line)
            i += 1
            continue
        if fence is not None:
            output.append(line)
            i += 1
            continue

        anchor = re.fullmatch(r'\s*<a id="([^"]+)"></a>\s*', line)
        if anchor and i + 1 < len(lines):
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", lines[i + 1])
            if heading and visible_heading_slug(heading.group(2)) == anchor.group(1):
                i += 1
                continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2)
            if home_layout and previous_level == 1 and level == 1:
                level = 2
            elif previous_level and level > previous_level + 1:
                level = previous_level + 1
            output.append("#" * level + " " + title)
            previous_level = level
        else:
            output.append(line)
        i += 1

    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(output) + suffix


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize learner-facing Markdown heading and anchor structure.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    ns = parser.parse_args()

    changed: list[str] = []
    for path in markdown_sources():
        relative = path.relative_to(ROOT).as_posix()
        before = path.read_text(encoding="utf-8")
        after = normalize(before, relative=relative)
        if before == after:
            continue
        changed.append(relative)
        if ns.write:
            path.write_text(after, encoding="utf-8")

    for relative in changed:
        print(f"MARKDOWN_STRUCTURE_CHANGE={relative}")
    if ns.check and changed:
        print(f"MARKDOWN_STRUCTURE_RESULT=FAIL changed={len(changed)}")
        return 1
    print(f"MARKDOWN_STRUCTURE_CHANGED={len(changed)}")
    print("MARKDOWN_STRUCTURE_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
