#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{relative}: expected one occurrence, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    "scripts/site_inventory.py",
    '''    if source == "docs/index.md":\n        hero = re.search(r'(?m)^  name:\\s*["\\'](.+?)["\\']\\s*$', text)\n        if hero:\n            return hero.group(1).strip()\n''',
    '''    if source == "docs/index.md":\n        hero_name = re.search(r'(?m)^  name:\\s*["\\'](.+?)["\\']\\s*$', text)\n        hero_text = re.search(r'(?m)^  text:\\s*["\\'](.+?)["\\']\\s*$', text)\n        if hero_name:\n            return " ".join(\n                part.strip()\n                for part in (hero_name.group(1), hero_text.group(1) if hero_text else "")\n                if part.strip()\n            )\n''',
)

replace_once(
    "scripts/render_vitepress_pages.py",
    '''                          const emptyButtons = [...document.querySelectorAll('button')]\n                            .filter(visible).filter(button => !accessibleName(button));\n                          if (emptyButtons.length) failures.push(`visible buttons without accessible name: ${emptyButtons.length}`);\n''',
    '''                          const emptyButtons = [...document.querySelectorAll('button')]\n                            .filter(visible).filter(button => !accessibleName(button));\n                          if (emptyButtons.length) {\n                            const descriptions = emptyButtons.slice(0, 5).map(button => {\n                              const classes = [...button.classList].join('.');\n                              return button.tagName.toLowerCase() + (classes ? `.${classes}` : '') +\n                                ` html=${button.outerHTML.slice(0, 240)}`;\n                            });\n                            failures.push(`visible buttons without accessible name: ${emptyButtons.length}: ${descriptions.join(' | ')}`);\n                          }\n''',
)

replace_once(
    "scripts/render_vitepress_pages.py",
    '''                          const interactiveSelector = 'a[href],button,input:not([type="hidden"]),select,textarea,summary,[tabindex]';\n                          const isInteractive = element => {\n                            if (!(element instanceof Element)) return false;\n                            if (element.matches('a[href],button,input:not([type="hidden"]),select,textarea,summary')) return true;\n                            const tabindex = element.getAttribute('tabindex');\n                            return tabindex !== null && Number(tabindex) >= 0;\n                          };\n''',
    '''                          const interactiveSelector = 'a[href],button,input:not([type="hidden"]),select,textarea,summary,[role="button"],[role="link"],[role="checkbox"],[role="radio"],[role="switch"],[role="menuitem"],[role="option"]';\n                          const isInteractive = element => element instanceof Element && element.matches(interactiveSelector);\n''',
)

print("BROWSER_AUDIT_CODE_REPAIRS=PASS")
