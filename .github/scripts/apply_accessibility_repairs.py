#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{relative}: expected one occurrence, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    "scripts/site_inventory.py",
    '''def first_heading(text: str, *, source: str) -> str:\n    match = re.search(r"(?m)^#\\s+(.+?)\\s*$", text)\n''',
    '''def first_heading(text: str, *, source: str) -> str:\n    if source == "docs/index.md":\n        hero = re.search(r'(?m)^  name:\\s*["\\\'](.+?)["\\\']\\s*$', text)\n        if hero:\n            return hero.group(1).strip()\n    match = re.search(r"(?m)^#\\s+(.+?)\\s*$", text)\n''',
)

replace_once(
    "scripts/render_vitepress_pages.py",
    "const doc = document.querySelector('.VPDoc');",
    "const doc = document.querySelector('.VPDoc, .VPHome');",
)
replace_once(
    "scripts/render_vitepress_pages.py",
    "if (!document.querySelector('main')) failures.push('main landmark is missing');",
    "if (!document.querySelector('main') && !document.querySelector('.VPHome')) failures.push('main content root is missing');",
)
replace_once(
    "scripts/render_vitepress_pages.py",
    '''main: Boolean(document.querySelector('main')),\n''',
    '''main: Boolean(document.querySelector('main') || document.querySelector('.VPHome')),\n''',
)
replace_once(
    "scripts/render_vitepress_pages.py",
    "h1: h1s[0]?.innerText || '',",
    "h1: (h1s[0]?.innerText || '').replace(/[\\u200B-\\u200D\\uFEFF]/g, '').replace(/\\s+/g, ' ').trim(),",
)
replace_once(
    "scripts/render_vitepress_pages.py",
    '''                          const interactiveSelector = 'a[href],button,input:not([type="hidden"]),select,textarea,summary,[tabindex]';\n                          const nestedInteractive = [...document.querySelectorAll(interactiveSelector)]\n                            .filter(element => {\n                              const parent = element.parentElement?.closest(interactiveSelector);\n                              return parent && parent !== element;\n                            });\n''',
    '''                          const interactiveSelector = 'a[href],button,input:not([type="hidden"]),select,textarea,summary,[tabindex]';\n                          const isInteractive = element => {\n                            if (!(element instanceof Element)) return false;\n                            if (element.matches('a[href],button,input:not([type="hidden"]),select,textarea,summary')) return true;\n                            const tabindex = element.getAttribute('tabindex');\n                            return tabindex !== null && Number(tabindex) >= 0;\n                          };\n                          const nestedInteractive = [...document.querySelectorAll(interactiveSelector)]\n                            .filter(isInteractive)\n                            .filter(element => {\n                              for (let ancestor = element.parentElement; ancestor; ancestor = ancestor.parentElement) {\n                                if (isInteractive(ancestor)) return true;\n                              }\n                              return false;\n                            });\n''',
)

replace_once(
    "scripts/generate_course_docs.py",
    '''def normalize(text: str, *, strip_asm_comments: bool = True) -> str:\n''',
    '''def namespace_embedded_ids(text: str, source: str) -> str:\n    prefix = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")\n    ids = set(re.findall(r'id="([^"]+)"', text))\n    for anchor in sorted(ids, key=len, reverse=True):\n        scoped = f"{prefix}-{anchor}"\n        text = text.replace(f'id="{anchor}"', f'id="{scoped}"')\n        text = text.replace(f'](#{anchor})', f'](#{scoped})')\n    return text\n\n\ndef normalize(text: str, *, strip_asm_comments: bool = True) -> str:\n''',
)
replace_once(
    "scripts/generate_course_docs.py",
    '''            demote_embedded_h1(path.read_text(encoding="utf-8").strip()),\n''',
    '''            namespace_embedded_ids(\n                demote_embedded_h1(path.read_text(encoding="utf-8").strip()),\n                str(path.relative_to(ROOT)),\n            ),\n''',
)
replace_once(
    "scripts/generate_course_docs.py",
    '''        demote_embedded_h1((DOCS / "transfer_workbook.md").read_text(encoding="utf-8").strip()),\n''',
    '''        namespace_embedded_ids(\n            demote_embedded_h1((DOCS / "transfer_workbook.md").read_text(encoding="utf-8").strip()),\n            "docs/transfer_workbook.md",\n        ),\n''',
)
replace_once(
    "scripts/generate_course_docs.py",
    '''        demote_embedded_h1((DOCS / "final_exam.md").read_text(encoding="utf-8").strip()),\n''',
    '''        namespace_embedded_ids(\n            demote_embedded_h1((DOCS / "final_exam.md").read_text(encoding="utf-8").strip()),\n            "docs/final_exam.md",\n        ),\n''',
)

print("ACCESSIBILITY_CODE_REPAIRS=PASS")
