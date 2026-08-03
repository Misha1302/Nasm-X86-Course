from __future__ import annotations

import html
import re
import unicodedata
from html.parser import HTMLParser


class _VisibleTextParser(HTMLParser):
    """Extract browser-visible text while ignoring comments and markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:  # pragma: no cover - convert_charrefs handles it
        self.parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:  # pragma: no cover - convert_charrefs handles it
        self.parts.append(html.unescape(f"&#{name};"))


def visible_text(source: str) -> str:
    """Approximate rendered Markdown/HTML text for leakage checks.

    The transformation is intentionally hostile to formatting-based obfuscation:
    HTML comments/tags disappear as they do in the browser, links retain their label,
    and common Markdown emphasis/code delimiters are removed.
    """

    source = html.unescape(source)
    source = re.sub(r"(?is)<!--.*?-->", "", source)
    source = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", source)
    source = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", source)

    parser = _VisibleTextParser()
    parser.feed(source)
    parser.close()
    text = "".join(parser.parts)

    # Remove presentation-only Markdown characters. Keep `_` because it is part of
    # assembly/C identifiers, but collapse escaped punctuation and zero-width chars.
    text = re.sub(r"\\([`*~\[\]()<>])", r"\1", text)
    text = text.replace("`", "").replace("*", "").replace("~", "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text


def normalize_visible(source: str) -> str:
    text = visible_text(source).lower()
    text = text.replace("dword ptr", "dword").replace("byte ptr", "byte").replace("word ptr", "word")
    return re.sub(r"[^a-z0-9_+%\[\]=<>!*/-]+", "", text)
