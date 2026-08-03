#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import ConsoleMessage, Error, Request, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "day_25": "День 25",
    "final_exam": "Финальный экзамен",
    "final_exam_keys": "Ключи",
    "checkpoints": "Контрольные точки",
    "checkpoint_keys": "Ключи",
    "transfer_workbook": "Перенос",
    "closed_book_workbook": "без встроенных ответов",
    "day_10": "День 10",
    "day_10_learning_path": "День 10",
}
VIEWPORTS = [
    ("desktop", 1440, 1000, 1.0, 100),
    ("mobile", 390, 844, 1.0, 100),
    ("zoom200", 360, 450, 2.0, 200),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render decision-critical pages from the real VitePress build.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", default=str(ROOT / "render-evidence" / "vitepress"))
    ns = parser.parse_args()

    output = Path(ns.output).resolve()
    shots = output / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    for old in shots.glob("*.png"):
        old.unlink()

    evidence: list[dict[str, object]] = []
    failures: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            for page_name, expected_text in PAGES.items():
                for label, width, height, scale, zoom_percent in VIEWPORTS:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=scale,
                    )
                    page = context.new_page()
                    page.set_default_timeout(20_000)
                    console_errors: list[str] = []
                    page_errors: list[str] = []
                    failed_requests: list[str] = []

                    def on_console(message: ConsoleMessage) -> None:
                        if message.type == "error":
                            console_errors.append(message.text)

                    def on_page_error(error: Error) -> None:
                        page_errors.append(str(error))

                    def on_request_failed(request: Request) -> None:
                        failure = request.failure
                        failed_requests.append(f"{request.method} {request.url}: {failure}")

                    page.on("console", on_console)
                    page.on("pageerror", on_page_error)
                    page.on("requestfailed", on_request_failed)

                    url = urljoin(ns.base_url.rstrip("/") + "/", page_name)
                    response = page.goto(url, wait_until="networkidle")
                    status = response.status if response else 0
                    page.wait_for_timeout(150)

                    metrics = page.evaluate(
                        """() => ({
                          title: document.title,
                          h1: document.querySelector('.VPDoc h1')?.innerText || '',
                          bodyText: document.querySelector('.VPDoc')?.innerText || '',
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
                        screenshot_paths.append(str(target.relative_to(output)))

                    item = {
                        "renderer": "vitepress-build-playwright",
                        "page": page_name,
                        "url": url,
                        "viewport": label,
                        "width": width,
                        "height": height,
                        "device_scale_factor": scale,
                        "browser_zoom_percent": zoom_percent,
                        "http_status": status,
                        "title": metrics["title"],
                        "h1": metrics["h1"],
                        "vp_doc": bool(metrics["doc"]),
                        "vp_nav": bool(metrics["nav"]),
                        "vp_sidebar": bool(metrics["sidebar"]),
                        "horizontal_overflow": overflow,
                        "tables": int(metrics["tables"]),
                        "code_blocks": int(metrics["codeBlocks"]),
                        "raw_anchor_text": bool(metrics["rawAnchorText"]),
                        "visible_open_details": int(metrics["visibleDetails"]),
                        "console_errors": console_errors,
                        "page_errors": page_errors,
                        "failed_requests": failed_requests,
                        "screenshots": screenshot_paths,
                    }
                    evidence.append(item)

                    prefix = f"{page_name}/{label}"
                    if status != 200:
                        failures.append(f"{prefix}: HTTP {status}")
                    if not metrics["doc"] or not metrics["nav"]:
                        failures.append(f"{prefix}: missing VitePress shell")
                    if expected_text.lower() not in str(metrics["bodyText"]).lower():
                        failures.append(f"{prefix}: expected visible text {expected_text!r} missing")
                    if overflow:
                        failures.append(f"{prefix}: horizontal overflow")
                    if metrics["rawAnchorText"]:
                        failures.append(f"{prefix}: raw anchor text")
                    if page_name == "closed_book_workbook" and int(metrics["visibleDetails"]) != 0:
                        failures.append(f"{prefix}: open solution details in closed-book page")
                    for message in console_errors:
                        failures.append(f"{prefix}: console error: {message}")
                    for message in page_errors:
                        failures.append(f"{prefix}: page error: {message}")
                    for message in failed_requests:
                        failures.append(f"{prefix}: request failed: {message}")
                    context.close()
        finally:
            browser.close()

    output.mkdir(parents=True, exist_ok=True)
    (output / "visual_evidence.json").write_text(
        json.dumps({"cases": evidence, "failures": failures}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"VITEPRESS_VISUAL_CASES={len(evidence)}")
    print(f"VITEPRESS_VISUAL_SCREENSHOTS={sum(len(item['screenshots']) for item in evidence)}")
    print(f"VITEPRESS_VISUAL_FAILURES={len(failures)}")
    for failure in failures:
        print(f"VITEPRESS_VISUAL_FAILURE={failure}")
    print("VITEPRESS_VISUAL_RESULT=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
