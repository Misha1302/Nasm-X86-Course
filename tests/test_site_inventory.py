#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from site_inventory import discover_site_pages, normalize_internal_route  # noqa: E402

CONFIG = ROOT / "docs" / ".vitepress" / "config.mts"
THEME = ROOT / "docs" / ".vitepress" / "theme" / "index.ts"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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
    print("SITE_INVENTORY_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
