from __future__ import annotations

import json
from pathlib import Path

import mistune
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "render-evidence"
SITE = OUT / "site"
SHOTS = OUT / "screenshots"
PAGES = [
    "day_25",
    "final_exam",
    "final_exam_keys",
    "checkpoints",
    "checkpoint_keys",
    "transfer_workbook",
    "closed_book_workbook",
    "day_10",
    "day_10_learning_path",
]
VIEWPORTS = [
    ("desktop", 1440, 1000, 1),
    ("mobile", 390, 844, 1),
    ("zoom200", 720, 900, 2),
]


def md_to_html(text: str) -> str:
    markdown = mistune.create_markdown(escape=False, plugins=["table", "strikethrough", "task_lists"])
    return markdown(text)


def main() -> int:
    SITE.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    for old in SHOTS.glob("*.png"):
        old.unlink()

    css = """
body{font-family:system-ui,sans-serif;max-width:920px;margin:0 auto;padding:32px;line-height:1.55;color:#222}
pre{overflow:auto;background:#f5f5f5;padding:16px;border-radius:8px;white-space:pre}
code{overflow-wrap:anywhere} table{width:100%;table-layout:fixed;border-collapse:collapse}
td,th{border:1px solid #bbb;padding:6px;overflow-wrap:anywhere}
a{color:#3451b2} img{max-width:100%}
@media(max-width:520px){body{padding:14px}table{font-size:11px}td,th{padding:3px}}
"""
    html_by_page: dict[str, str] = {}
    for name in PAGES:
        md = (ROOT / "docs" / f"{name}.md").read_text(encoding="utf-8")
        rendered = (
            '<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<style>{css}</style></head><body>{md_to_html(md)}</body></html>"
        )
        html_by_page[name] = rendered
        (SITE / f"{name}.html").write_text(rendered, encoding="utf-8")

    evidence: list[dict[str, object]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            for name in PAGES:
                for label, width, height, zoom in VIEWPORTS:
                    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                    page.set_default_timeout(15_000)
                    page.set_content(html_by_page[name], wait_until="domcontentloaded")
                    if zoom != 1:
                        page.evaluate("z => { document.body.style.zoom = String(z); }", zoom)
                    metrics = page.evaluate(
                        """() => ({
                            clientWidth: document.documentElement.clientWidth,
                            scrollWidth: document.documentElement.scrollWidth,
                            scrollHeight: document.documentElement.scrollHeight,
                            tables: document.querySelectorAll('table').length,
                            codeBlocks: document.querySelectorAll('pre').length,
                            links: document.querySelectorAll('a').length,
                            rawAnchors: [...document.body.childNodes].some(n => n.nodeType === Node.TEXT_NODE && n.textContent.includes('<a id='))
                        })"""
                    )
                    max_y = max(0, int(metrics["scrollHeight"]) - height)
                    positions = [("top", 0)]
                    if max_y > 0:
                        positions.append(("middle", max_y // 2))
                        positions.append(("bottom", max_y))
                    screenshots = []
                    for position, y in positions:
                        page.evaluate("y => window.scrollTo(0, y)", y)
                        page.wait_for_timeout(40)
                        shot = SHOTS / f"{name}-{label}-{position}.png"
                        page.screenshot(path=str(shot), full_page=False, animations="disabled", timeout=15_000)
                        screenshots.append(str(shot.relative_to(ROOT)))
                    evidence.append(
                        {
                            "renderer": "mistune+chromium-degraded-not-vitepress",
                            "page": name,
                            "viewport": label,
                            "width": width,
                            "height": height,
                            "zoom": zoom,
                            "horizontal_overflow": int(metrics["scrollWidth"]) > int(metrics["clientWidth"]) + 1,
                            "scroll_height": int(metrics["scrollHeight"]),
                            "tables": int(metrics["tables"]),
                            "code_blocks": int(metrics["codeBlocks"]),
                            "links": int(metrics["links"]),
                            "raw_anchor_text": bool(metrics["rawAnchors"]),
                            "screenshots": screenshots,
                        }
                    )
                    page.close()
        finally:
            browser.close()

    (OUT / "visual_evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    overflow = [item for item in evidence if item["horizontal_overflow"]]
    raw = [item for item in evidence if item["raw_anchor_text"]]
    print(f"VISUAL_CASES={len(evidence)}")
    print(f"VISUAL_SCREENSHOTS={sum(len(item['screenshots']) for item in evidence)}")
    print(f"VISUAL_OVERFLOW={len(overflow)}")
    print(f"VISUAL_RAW_ANCHORS={len(raw)}")
    print("VISUAL_RENDERER=DEGRADED_MISTUNE_CHROMIUM")
    return 1 if overflow or raw else 0


if __name__ == "__main__":
    raise SystemExit(main())
