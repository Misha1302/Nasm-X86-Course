from __future__ import annotations

from html.parser import HTMLParser
import html
import re


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_comment(self, data: str) -> None:
        return


def visible_text(source: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(source)
    parser.close()
    return html.unescape("".join(parser.parts))


def strip_asm_comments(source: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in source.splitlines())


def normalize_visible(source: str, *, strip_comments: bool = True) -> str:
    text = visible_text(source)
    if strip_comments:
        text = strip_asm_comments(text)
    text = text.lower()
    text = text.replace("dword ptr", "dword").replace("byte ptr", "byte").replace("word ptr", "word")
    return re.sub(r"[^a-z0-9_+%\[\]=<>!*/-]+", "", text)
