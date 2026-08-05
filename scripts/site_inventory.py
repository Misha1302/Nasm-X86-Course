#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


@dataclass(frozen=True, slots=True)
class SitePage:
    source: str
    route: str
    heading: str
    generated: bool


GENERATED_SOURCES = {
    "docs/textbook.md",
    "docs/course_migration.md",
    "docs/closed_book_workbook.md",
}


def route_for_source(path: Path, *, docs_root: Path = DOCS) -> str:
    relative = path.relative_to(docs_root)
    if relative.suffix != ".md":
        raise ValueError(f"not a Markdown page: {relative}")
    stem = relative.with_suffix("").as_posix()
    if stem == "index":
        return ""
    if stem.endswith("/index"):
        return stem[: -len("index")]
    return stem


def first_heading(text: str, *, source: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if not match:
        raise ValueError(f"page lacks H1 heading: {source}")
    heading = match.group(1)
    heading = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[`*_~]", "", heading).strip()
    if not heading:
        raise ValueError(f"page has an empty H1 heading: {source}")
    return heading


def discover_site_pages(*, docs_root: Path = DOCS, root: Path = ROOT) -> tuple[SitePage, ...]:
    if not docs_root.is_dir():
        raise FileNotFoundError(f"docs directory does not exist: {docs_root}")

    pages: list[SitePage] = []
    by_route: dict[str, str] = {}
    for path in sorted(docs_root.rglob("*.md")):
        relative_to_docs = path.relative_to(docs_root)
        if any(part.startswith(".") for part in relative_to_docs.parts):
            continue
        source = path.relative_to(root).as_posix()
        route = route_for_source(path, docs_root=docs_root)
        previous = by_route.get(route)
        if previous is not None:
            raise ValueError(f"route collision {route!r}: {previous} and {source}")
        by_route[route] = source
        pages.append(
            SitePage(
                source=source,
                route=route,
                heading=first_heading(path.read_text(encoding="utf-8"), source=source),
                generated=source in GENERATED_SOURCES,
            )
        )

    if not pages:
        raise ValueError("site inventory is empty")
    if "" not in by_route:
        raise ValueError("site inventory lacks docs/index.md root route")
    return tuple(pages)


def normalize_internal_route(link: str) -> str | None:
    value = link.strip()
    if not value or value.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
    value = value.split("#", 1)[0].split("?", 1)[0]
    if not value:
        return None
    value = value.lstrip("/")
    if value == "index":
        return ""
    if value.endswith("/index"):
        return value[: -len("index")]
    return value


if __name__ == "__main__":
    pages = discover_site_pages()
    print(f"SITE_PAGE_COUNT={len(pages)}")
    print(f"SITE_GENERATED_PAGE_COUNT={sum(page.generated for page in pages)}")
    for page in pages:
        print(f"{page.route or '/'}\t{page.source}\t{page.heading}")
