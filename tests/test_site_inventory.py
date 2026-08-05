#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_markdown_structure import markdown_sources, normalize  # noqa: E402
from site_inventory import discover_site_pages, normalize_internal_route  # noqa: E402

CONFIG = ROOT / "docs" / ".vitepress" / "config.mts"
THEME = ROOT / "docs" / ".vitepress" / "theme" / "index.ts"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def markdown_h1_count(path: Path) -> int:
    in_fence: str | None = None
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else ("~~~" if stripped.startswith("~~~") else None)
        if marker is not None:
            if in_fence is None:
                in_fence = marker
            elif in_fence == marker:
                in_fence = None
            continue
        if in_fence is None and line.startswith("# "):
            count += 1
    return count


def main() -> int:
    pages = discover_site_pages()
    routes = {page.route for page in pages}
    sources = {page.source for page in pages}

    require(len(pages) >= 50, f"site inventory unexpectedly small: {len(pages)}")
    for source in (
        "docs/index.md",
        "docs/day_01.md",
        "docs/day_25.md",
        "docs/textbook.md",
        "docs/patterns/branchless.md",
        "docs/patterns/bigint.md",
        "docs/tasks/index.md",
        "docs/tasks/spring-01/01-04-books.md",
    ):
        require(source in sources, f"site inventory lacks learner-facing page {source}")

    structure_drift: list[str] = []
    for path in markdown_sources():
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if normalize(text, relative=relative) != text:
            structure_drift.append(relative)
    require(not structure_drift, f"Markdown structure requires normalization: {structure_drift}")

    for relative in (
        "docs/textbook.md",
        "docs/closed_book_workbook.md",
        "docs/course_migration.md",
    ):
        count = markdown_h1_count(ROOT / relative)
        require(count == 1, f"generated compound page {relative} has {count} Markdown H1 headings")

    config = CONFIG.read_text(encoding="utf-8")
    theme = THEME.read_text(encoding="utf-8")
    require(
        'lang: "ru-RU"' in config or 'document.documentElement.lang = "ru-RU"' in theme,
        "VitePress must establish the Russian document language",
    )

    links = re.findall(r'\blink:\s*"([^"]+)"', config)
    require(links, "VitePress config contains no navigation links")
    for link in links:
        route = normalize_internal_route(link)
        if route is None:
            continue
        require(route in routes, f"navigation link {link!r} has no Markdown route")

    route_by_source = {page.source: page.route for page in pages}
    for source, expected in (
        ("docs/index.md", ""),
        ("docs/patterns/index.md", "patterns/"),
        ("docs/tasks/index.md", "tasks/"),
        ("docs/day_01.md", "day_01"),
    ):
        require(route_by_source.get(source) == expected, f"route mapping drifted for {source}")

    print(f"SITE_INVENTORY_PAGES={len(pages)}")
    print(f"SITE_INVENTORY_NAV_LINKS={len(links)}")
    print("SITE_MARKDOWN_STRUCTURE=PASS")
    print("SITE_GENERATED_SINGLE_H1=PASS")
    print("SITE_INVENTORY_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
