#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
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
    # label, CSS viewport width/height, device scale factor, browser zoom percent
    ("desktop", 1440, 1000, 1.0, 100),
    ("mobile", 390, 844, 1.0, 100),
    # Browser zoom reduces the CSS viewport instead of scaling the document box.
    # device_scale_factor=2 preserves 720x900 physical screenshot evidence.
    ("zoom200", 360, 450, 2.0, 200),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render decision-critical pages from the real VitePress preview.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", default=str(ROOT / "render-evidence" / "vitepress"))
    ns = parser.parse_args()

    out = Path(ns.output).resolve()
    shots = out / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    for old in shots.glob("*.png"):
        old.unlink()

    evidence: list[dict[str, object]] = []
    failures: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for page_name in PAGES:
                for label, width, height, device_scale_factor, zoom_percent in VIEWPORTS:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=device_scale_factor,
                    )
                    page = context.new_page()
                    page.set_default_timeout(20_000)
                    url = urljoin(ns.base_url.rstrip("/") + "/", page_name)
                    response = page.goto(url, wait_until="networkidle")
                    status = response.status if response else 0
                    page.wait_for_timeout(150)

                    metrics = page.evaluate(
                        """() => ({
                          title: document.title,
                          clientWidth: document.documentElement.clientWidth,
                          scrollWidth: document.documentElement.scrollWidth,
                          scrollHeight: document.documentElement.scrollHeight,
                          doc: Boolean(document.querySelector('.VPDoc')),
                          nav: Boolean(document.querySelector('.VPNav')),
                          sidebar: Boolean(document.querySelector('.VPSidebar')),
                          tables: document.querySelectorAll('.VPDoc table').length,
                          codeBlocks: document.querySelectorAll('.VPDoc pre').length,
                          rawAnchorText: document.body.innerText.includes('<a id='),
                          visibleDetails: [...document.querySelectorAll('details')].filter(x => x.open).length
                        })"""
                    )
                    overflow = int(metrics["scrollWidth"]) > int(metrics["clientWidth"]) + 1
                    max_y = max(0, int(metrics["scrollHeight"]) - height)
                    positions = [("top", 0)]
                    if max_y:
                        positions.extend([("middle", max_y // 2), ("bottom", max_y)])
                    screenshot_paths: list[str] = []
                    for position, y in positions:
                        page.evaluate("y => window.scrollTo(0, y)", y)
                        page.wait_for_timeout(80)
                        target = shots / f"{page_name}-{label}-{position}.png"
                        page.screenshot(path=str(target), full_page=False, animations="disabled")
                        screenshot_paths.append(str(target.relative_to(out)))

                    item = {
                        "renderer": "vitepress-preview-playwright",
                        "page": page_name,
                        "url": url,
                        "viewport": label,
                        "width": width,
                        "height": height,
                        "device_scale_factor": device_scale_factor,
                        "browser_zoom_percent": zoom_percent,
                        "http_status": status,
                        "title": metrics["title"],
                        "vp_doc": bool(metrics["doc"]),
                        "vp_nav": bool(metrics["nav"]),
                        "vp_sidebar": bool(metrics["sidebar"]),
                        "horizontal_overflow": overflow,
                        "tables": int(metrics["tables"]),
                        "code_blocks": int(metrics["codeBlocks"]),
                        "raw_anchor_text": bool(metrics["rawAnchorText"]),
                        "visible_open_details": int(metrics["visibleDetails"]),
                        "screenshots": screenshot_paths,
                    }
                    evidence.append(item)
                    if status != 200:
                        failures.append(f"{page_name}/{label}: HTTP {status}")
                    if not metrics["doc"] or not metrics["nav"]:
                        failures.append(f"{page_name}/{label}: missing VitePress shell")
                    if overflow:
                        failures.append(f"{page_name}/{label}: horizontal overflow")
                    if metrics["rawAnchorText"]:
                        failures.append(f"{page_name}/{label}: raw anchor text")
                    context.close()
        finally:
            browser.close()

    out.mkdir(parents=True, exist_ok=True)
    (out / "visual_evidence.json").write_text(
        json.dumps({"cases": evidence, "failures": failures}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"VITEPRESS_VISUAL_CASES={len(evidence)}")
    print(f"VITEPRESS_VISUAL_SCREENSHOTS={sum(len(x['screenshots']) for x in evidence)}")
    print(f"VITEPRESS_VISUAL_FAILURES={len(failures)}")
    for failure in failures:
        print(f"VITEPRESS_VISUAL_FAILURE={failure}")
    print("VITEPRESS_VISUAL_RESULT=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
