#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "scripts" / "render_vitepress_pages.py"
text = path.read_text(encoding="utf-8")
old = '''                          while (Date.now() < deadline) {\n                            const switches = [...document.querySelectorAll('.VPSwitchAppearance')];\n                            const ready = switches.length === 0 || switches.every(button =>\n                              (button.getAttribute('aria-label') || button.getAttribute('title') || '').trim()\n                            );\n'''
new = '''                          while (Date.now() < deadline) {\n                            const switches = [...document.querySelectorAll('.VPSwitchAppearance')].filter(button => {\n                              const style = getComputedStyle(button);\n                              const rect = button.getBoundingClientRect();\n                              return style.display !== 'none' && style.visibility !== 'hidden' &&\n                                Number.parseFloat(style.opacity || '1') !== 0 &&\n                                rect.width > 0 && rect.height > 0;\n                            });\n                            const ready = switches.length === 0 || switches.every(button =>\n                              (button.getAttribute('aria-label') || button.getAttribute('title') || '').trim()\n                            );\n'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one hydration switch loop, found {count}")
path.write_text(text.replace(old, new), encoding="utf-8")
print("VISIBLE_HYDRATION_READINESS=PASS")
