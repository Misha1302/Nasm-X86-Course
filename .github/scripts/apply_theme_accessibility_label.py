#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "docs" / ".vitepress" / "config.mts"
text = path.read_text(encoding="utf-8")
old = '''    themeConfig: {\n        nav: [\n'''
new = '''    themeConfig: {\n        darkModeSwitchLabel: "Оформление",\n        lightModeSwitchTitle: "Переключить на светлую тему",\n        darkModeSwitchTitle: "Переключить на тёмную тему",\n\n        nav: [\n'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected exactly one themeConfig/nav boundary, found {count}")
path.write_text(text.replace(old, new), encoding="utf-8")
print("THEME_ACCESSIBILITY_LABEL=PASS")
