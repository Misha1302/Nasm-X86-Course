#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "scripts" / "render_vitepress_pages.py"
text = path.read_text(encoding="utf-8")
old = '''                    status = response.status if response else 0\n                    page.wait_for_timeout(120)\n\n                    metrics = page.evaluate(\n'''
new = '''                    status = response.status if response else 0\n                    page.wait_for_timeout(120)\n                    appearance_switch_ready = page.evaluate(\n                        r"""async () => {\n                          const deadline = Date.now() + 10_000;\n                          while (Date.now() < deadline) {\n                            const switches = [...document.querySelectorAll('.VPSwitchAppearance')];\n                            const ready = switches.length === 0 || switches.every(button =>\n                              (button.getAttribute('aria-label') || button.getAttribute('title') || '').trim()\n                            );\n                            if (ready) return true;\n                            await new Promise(resolve => setTimeout(resolve, 50));\n                          }\n                          return false;\n                        }"""\n                    )\n                    if not appearance_switch_ready:\n                        page_errors.append(\n                            "appearance switch did not receive an accessible name after hydration"\n                        )\n\n                    metrics = page.evaluate(\n'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one render readiness boundary, found {count}")
path.write_text(text.replace(old, new), encoding="utf-8")
print("HYDRATION_READINESS_REPAIR=PASS")
