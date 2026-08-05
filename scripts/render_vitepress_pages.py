#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from urllib.parse import urljoin

from evidence_provenance import digest_paths
from playwright.sync_api import ConsoleMessage, Error, Request, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "day_25": "День 25",
    "final_exam": "Финальный экзамен",
    "final_exam_keys": "Ключ и рубрика финального экзамена",
    "checkpoints": "Контрольные точки",
    "checkpoint_keys": "Ключи",
    "transfer_workbook": "Перенос",
    "closed_book_workbook": "без встроенных ответов",
    "day_10": "День 10",
    "day_10_learning_path": "День 10",
}

# Browser page zoom changes the effective CSS viewport and therefore responsive
# media queries. Applying CSS `zoom` to <html> does not: it leaves the layout
# viewport at the unzoomed width and can create false overflow in responsive
# shells. The zoom200 case models a 720x900 physical viewport at 200% page zoom
# as a 360x450 CSS viewport rendered at 2x raster scale. This is the observable
# reflow state a browser exposes to page layout and media queries.
VIEWPORTS = [
    {
        "label": "desktop",
        "css_width": 1440,
        "css_height": 1000,
        "raster_scale": 1.0,
        "zoom_percent": 100,
        "physical_width": 1440,
        "physical_height": 1000,
        "zoom_emulation": "native-css-viewport",
    },
    {
        "label": "mobile",
        "css_width": 390,
        "css_height": 844,
        "raster_scale": 1.0,
        "zoom_percent": 100,
        "physical_width": 390,
        "physical_height": 844,
        "zoom_emulation": "native-css-viewport",
    },
    {
        "label": "zoom200",
        "css_width": 360,
        "css_height": 450,
        "raster_scale": 2.0,
        "zoom_percent": 200,
        "physical_width": 720,
        "physical_height": 900,
        "zoom_emulation": "effective-css-viewport",
    },
]


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG file: {path}")
    return struct.unpack(">II", header[16:24])


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
                for viewport in VIEWPORTS:
                    label = str(viewport["label"])
                    width = int(viewport["css_width"])
                    height = int(viewport["css_height"])
                    raster_scale = float(viewport["raster_scale"])
                    zoom_percent = int(viewport["zoom_percent"])
                    expected_physical_width = int(viewport["physical_width"])
                    expected_physical_height = int(viewport["physical_height"])
                    zoom_emulation = str(viewport["zoom_emulation"])

                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=raster_scale,
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
                          innerWidth: window.innerWidth,
                          devicePixelRatio: window.devicePixelRatio,
                          visualViewportWidth: window.visualViewport?.width || 0,
                          visualViewportScale: window.visualViewport?.scale || 0,
                          narrowMediaQuery: window.matchMedia('(max-width: 767px)').matches,
                          doc: Boolean(document.querySelector('.VPDoc')),
                          nav: Boolean(document.querySelector('.VPNav')),
                          sidebar: Boolean(document.querySelector('.VPSidebar')),
                          tables: document.querySelectorAll('.VPDoc table').length,
                          codeBlocks: document.querySelectorAll('.VPDoc pre').length,
                          rawAnchorText: document.body.innerText.includes('<a id='),
                          visibleDetails: [...document.querySelectorAll('details')].filter(x => x.open).length
                        })"""
                    )
                    viewport_model_valid = (
                        int(metrics["clientWidth"]) == width
                        and int(metrics["innerWidth"]) == width
                        and abs(float(metrics["visualViewportWidth"]) - width) < 0.01
                        and abs(float(metrics["visualViewportScale"]) - 1.0) < 0.01
                        and abs(float(metrics["devicePixelRatio"]) - raster_scale) < 0.01
                        and expected_physical_width == round(width * raster_scale)
                        and expected_physical_height == round(height * raster_scale)
                    )
                    if label == "zoom200":
                        viewport_model_valid = (
                            viewport_model_valid
                            and zoom_percent == 200
                            and width == 360
                            and height == 450
                            and raster_scale == 2.0
                            and bool(metrics["narrowMediaQuery"])
                        )

                    root_scroll_overflow = int(metrics["scrollWidth"]) > int(metrics["clientWidth"]) + 1
                    max_y = max(0, int(metrics["scrollHeight"]) - height)
                    positions = [("top", 0)]
                    if max_y:
                        positions.extend([("middle", max_y // 2), ("bottom", max_y)])
                    screenshot_paths: list[str] = []
                    screenshot_dimensions: list[dict[str, object]] = []
                    overflow_observations: list[dict[str, object]] = []
                    for position, y in positions:
                        page.evaluate("y => window.scrollTo(0, y)", y)
                        page.wait_for_timeout(80)
                        visible_overflow = page.evaluate(
                            """() => {
                              const viewportWidth = window.visualViewport?.width || window.innerWidth;
                              const viewportHeight = window.visualViewport?.height || window.innerHeight;
                              const selector = element => {
                                if (element.id) return `${element.tagName.toLowerCase()}#${element.id}`;
                                const classes = [...element.classList].slice(0, 3).join('.');
                                return element.tagName.toLowerCase() + (classes ? `.${classes}` : '');
                              };
                              const insideHorizontalScroller = element => {
                                for (let ancestor = element.parentElement; ancestor; ancestor = ancestor.parentElement) {
                                  const style = getComputedStyle(ancestor);
                                  if ((style.overflowX === 'auto' || style.overflowX === 'scroll') &&
                                      ancestor.scrollWidth > ancestor.clientWidth + 1) {
                                    return true;
                                  }
                                }
                                return false;
                              };
                              const offenders = [];
                              for (const element of document.body.querySelectorAll('*')) {
                                if (element.closest('[hidden], [inert], [aria-hidden="true"]')) continue;
                                const style = getComputedStyle(element);
                                if (style.display === 'none' || style.visibility === 'hidden' ||
                                    Number.parseFloat(style.opacity || '1') === 0) continue;
                                const rect = element.getBoundingClientRect();
                                if (rect.width <= 1 || rect.height <= 1) continue;
                                if (rect.bottom <= 0 || rect.top >= viewportHeight ||
                                    rect.right <= 0 || rect.left >= viewportWidth) continue;
                                if (insideHorizontalScroller(element)) continue;
                                if (rect.left < -1 || rect.right > viewportWidth + 1) {
                                  offenders.push({
                                    selector: selector(element),
                                    left: Math.round(rect.left * 100) / 100,
                                    right: Math.round(rect.right * 100) / 100,
                                    width: Math.round(rect.width * 100) / 100,
                                    position: style.position,
                                    overflowX: style.overflowX
                                  });
                                  if (offenders.length >= 20) break;
                                }
                              }
                              return { viewportWidth, viewportHeight, offenders };
                            }"""
                        )
                        overflow_observations.append(
                            {
                                "position": position,
                                "scroll_y": y,
                                "viewport_width": float(visible_overflow["viewportWidth"]),
                                "viewport_height": float(visible_overflow["viewportHeight"]),
                                "offenders": visible_overflow["offenders"],
                            }
                        )
                        target = shots / f"{page_name}-{label}-{position}.png"
                        page.screenshot(path=str(target), full_page=False, animations="disabled")
                        pixel_width, pixel_height = png_dimensions(target)
                        screenshot_paths.append(str(target.relative_to(output)))
                        screenshot_dimensions.append(
                            {
                                "path": str(target.relative_to(output)),
                                "pixel_width": pixel_width,
                                "pixel_height": pixel_height,
                            }
                        )
                        if (pixel_width, pixel_height) != (
                            expected_physical_width,
                            expected_physical_height,
                        ):
                            failures.append(
                                f"{page_name}/{label}: screenshot {position} is "
                                f"{pixel_width}x{pixel_height}, expected "
                                f"{expected_physical_width}x{expected_physical_height}"
                            )

                    visible_overflow_detected = any(
                        observation["offenders"] for observation in overflow_observations
                    )
                    horizontal_overflow = root_scroll_overflow or visible_overflow_detected
                    item = {
                        "renderer": "vitepress-build-playwright",
                        "page": page_name,
                        "url": url,
                        "viewport": label,
                        "css_width": width,
                        "css_height": height,
                        "raster_scale": raster_scale,
                        "physical_width": expected_physical_width,
                        "physical_height": expected_physical_height,
                        "zoom_percent": zoom_percent,
                        "zoom_emulation": zoom_emulation,
                        "viewport_model_valid": viewport_model_valid,
                        "inner_width": int(metrics["innerWidth"]),
                        "client_width": int(metrics["clientWidth"]),
                        "visual_viewport_width": float(metrics["visualViewportWidth"]),
                        "visual_viewport_scale": float(metrics["visualViewportScale"]),
                        "device_pixel_ratio": float(metrics["devicePixelRatio"]),
                        "narrow_media_query": bool(metrics["narrowMediaQuery"]),
                        "http_status": status,
                        "title": metrics["title"],
                        "h1": metrics["h1"],
                        "vp_doc": bool(metrics["doc"]),
                        "vp_nav": bool(metrics["nav"]),
                        "vp_sidebar": bool(metrics["sidebar"]),
                        "root_scroll_overflow": root_scroll_overflow,
                        "visible_overflow_detected": visible_overflow_detected,
                        "horizontal_overflow": horizontal_overflow,
                        "visible_overflow_observations": overflow_observations,
                        "tables": int(metrics["tables"]),
                        "code_blocks": int(metrics["codeBlocks"]),
                        "raw_anchor_text": bool(metrics["rawAnchorText"]),
                        "visible_open_details": int(metrics["visibleDetails"]),
                        "console_errors": console_errors,
                        "page_errors": page_errors,
                        "failed_requests": failed_requests,
                        "screenshots": screenshot_paths,
                        "screenshot_dimensions": screenshot_dimensions,
                    }
                    evidence.append(item)

                    prefix = f"{page_name}/{label}"
                    if status != 200:
                        failures.append(f"{prefix}: HTTP {status}")
                    if not metrics["doc"] or not metrics["nav"]:
                        failures.append(f"{prefix}: missing VitePress shell")
                    if expected_text.lower() not in str(metrics["bodyText"]).lower():
                        failures.append(f"{prefix}: expected visible text {expected_text!r} missing")
                    if not viewport_model_valid:
                        failures.append(f"{prefix}: viewport/zoom emulation is invalid")
                    if horizontal_overflow:
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
    source_digest = digest_paths(
        ROOT,
        [
            "scripts/render_vitepress_pages.py",
            "scripts/serve_built_site.py",
            "package.json",
            "package-lock.json",
            "docs/.vitepress/theme/style.css",
        ],
    )
    (output / "visual_evidence.json").write_text(
        json.dumps(
            {"source_digest": source_digest, "cases": evidence, "failures": failures},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"VITEPRESS_VISUAL_SOURCE_DIGEST={source_digest}")
    print(f"VITEPRESS_VISUAL_CASES={len(evidence)}")
    print(f"VITEPRESS_VISUAL_SCREENSHOTS={sum(len(item['screenshots']) for item in evidence)}")
    print(f"VITEPRESS_VISUAL_FAILURES={len(failures)}")
    for failure in failures:
        print(f"VITEPRESS_VISUAL_FAILURE={failure}")
    print("VITEPRESS_VISUAL_RESULT=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
