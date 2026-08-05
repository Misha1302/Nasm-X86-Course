#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from urllib.parse import urljoin

from evidence_provenance import digest_paths
from playwright.sync_api import ConsoleMessage, Error, Request, sync_playwright
from site_inventory import SitePage, discover_site_pages

ROOT = Path(__file__).resolve().parents[1]

# Every Markdown route is loaded at every viewport. These decision-critical pages
# additionally receive middle and bottom screenshots; all other pages still have
# overflow and accessibility checks at top/middle/bottom, plus a top screenshot.
DECISION_CRITICAL_ROUTES = {
    "day_10",
    "day_10_learning_path",
    "day_25",
    "final_exam",
    "final_exam_keys",
    "checkpoints",
    "checkpoint_keys",
    "transfer_workbook",
    "closed_book_workbook",
}

# Browser page zoom changes the effective CSS viewport and therefore responsive
# media queries. Applying CSS `zoom` to <html> does not. The zoom200 case models
# a 720x900 physical viewport at 200% page zoom as a 360x450 CSS viewport rendered
# at 2x raster scale.
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


def route_slug(route: str) -> str:
    return (route.strip("/") or "index").replace("/", "__")


def page_url(base_url: str, site_page: SitePage) -> str:
    base = base_url.rstrip("/") + "/"
    return urljoin(base, site_page.route)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render and audit every learner-facing route from the real VitePress build."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", default=str(ROOT / "render-evidence" / "vitepress"))
    ns = parser.parse_args()

    pages = discover_site_pages()
    output = Path(ns.output).resolve()
    shots = output / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    for old in shots.glob("*.png"):
        old.unlink()

    evidence: list[dict[str, object]] = []
    failures: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            for site_page in pages:
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

                    url = page_url(ns.base_url, site_page)
                    response = page.goto(url, wait_until="networkidle")
                    status = response.status if response else 0
                    page.wait_for_timeout(120)
                    appearance_switch_ready = page.evaluate(
                        r"""async () => {
                          const deadline = Date.now() + 10_000;
                          while (Date.now() < deadline) {
                            const switches = [...document.querySelectorAll('.VPSwitchAppearance')];
                            const ready = switches.length === 0 || switches.every(button =>
                              (button.getAttribute('aria-label') || button.getAttribute('title') || '').trim()
                            );
                            if (ready) return true;
                            await new Promise(resolve => setTimeout(resolve, 50));
                          }
                          return false;
                        }"""
                    )
                    if not appearance_switch_ready:
                        page_errors.append(
                            "appearance switch did not receive an accessible name after hydration"
                        )

                    metrics = page.evaluate(
                        r"""() => {
                          const doc = document.querySelector('.VPDoc, .VPHome');
                          const visible = element => {
                            if (!(element instanceof Element)) return false;
                            if (element.closest('[hidden], [inert], [aria-hidden="true"]')) return false;
                            const style = getComputedStyle(element);
                            if (style.display === 'none' || style.visibility === 'hidden' ||
                                Number.parseFloat(style.opacity || '1') === 0) return false;
                            const rect = element.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                          };
                          const accessibleName = element => {
                            const labelledBy = (element.getAttribute('aria-labelledby') || '')
                              .split(/\s+/).filter(Boolean)
                              .map(id => document.getElementById(id)?.textContent || '').join(' ').trim();
                            const imageAlt = [...element.querySelectorAll('img')]
                              .map(image => image.getAttribute('alt') || '').join(' ').trim();
                            return (
                              element.getAttribute('aria-label') ||
                              labelledBy ||
                              element.getAttribute('alt') ||
                              element.getAttribute('title') ||
                              element.textContent ||
                              imageAlt ||
                              ''
                            ).replace(/\s+/g, ' ').trim();
                          };
                          const failures = [];
                          const lang = document.documentElement.lang || '';
                          if (!lang.toLowerCase().startsWith('ru')) failures.push(`document language is ${lang || 'missing'}, expected ru`);
                          if (!document.title.trim()) failures.push('document title is empty');
                          if (!document.querySelector('main') && !document.querySelector('.VPHome')) failures.push('main content root is missing');
                          const h1s = [...(doc?.querySelectorAll('h1') || [])].filter(visible);
                          if (h1s.length !== 1) failures.push(`visible document H1 count is ${h1s.length}, expected 1`);

                          const ids = [...(doc?.querySelectorAll('[id]') || [])].map(element => element.id).filter(Boolean);
                          const duplicateIds = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
                          if (duplicateIds.length) failures.push(`duplicate ids: ${duplicateIds.slice(0, 10).join(', ')}`);

                          const imagesWithoutAlt = [...(doc?.querySelectorAll('img') || [])]
                            .filter(visible).filter(image => !image.hasAttribute('alt'));
                          if (imagesWithoutAlt.length) failures.push(`images without alt: ${imagesWithoutAlt.length}`);

                          const emptyLinks = [...document.querySelectorAll('a[href]')]
                            .filter(visible).filter(link => !accessibleName(link));
                          if (emptyLinks.length) failures.push(`visible links without accessible name: ${emptyLinks.length}`);

                          const emptyButtons = [...document.querySelectorAll('button')]
                            .filter(visible).filter(button => !accessibleName(button));
                          if (emptyButtons.length) {
                            const descriptions = emptyButtons.slice(0, 5).map(button => {
                              const classes = [...button.classList].join('.');
                              return button.tagName.toLowerCase() + (classes ? `.${classes}` : '') +
                                ` html=${button.outerHTML.slice(0, 240)}`;
                            });
                            failures.push(`visible buttons without accessible name: ${emptyButtons.length}: ${descriptions.join(' | ')}`);
                          }

                          const controlsWithoutLabel = [...document.querySelectorAll('input:not([type="hidden"]), select, textarea')]
                            .filter(visible).filter(control => {
                              if (control.getAttribute('aria-label') || control.getAttribute('aria-labelledby')) return false;
                              if (control.labels && control.labels.length) return false;
                              return false === ['button', 'submit', 'reset', 'image'].includes(control.type);
                            });
                          if (controlsWithoutLabel.length) failures.push(`form controls without label: ${controlsWithoutLabel.length}`);

                          const positiveTabIndex = [...document.querySelectorAll('[tabindex]')]
                            .filter(element => Number(element.getAttribute('tabindex')) > 0);
                          if (positiveTabIndex.length) failures.push(`positive tabindex elements: ${positiveTabIndex.length}`);

                          const headings = [...(doc?.querySelectorAll('h1,h2,h3,h4,h5,h6') || [])].filter(visible);
                          let previousLevel = 0;
                          for (const heading of headings) {
                            const level = Number(heading.tagName.slice(1));
                            if (previousLevel && level > previousLevel + 1) {
                              failures.push(`heading level skips from H${previousLevel} to H${level}`);
                              break;
                            }
                            previousLevel = level;
                          }

                          const tablesWithoutHeaders = [...(doc?.querySelectorAll('table') || [])]
                            .filter(table => !table.querySelector('th'));
                          if (tablesWithoutHeaders.length) failures.push(`tables without header cells: ${tablesWithoutHeaders.length}`);

                          const detailsWithoutSummary = [...(doc?.querySelectorAll('details') || [])]
                            .filter(details => !details.querySelector(':scope > summary'));
                          if (detailsWithoutSummary.length) failures.push(`details without summary: ${detailsWithoutSummary.length}`);

                          const interactiveSelector = 'a[href],button,input:not([type="hidden"]),select,textarea,summary,[role="button"],[role="link"],[role="checkbox"],[role="radio"],[role="switch"],[role="menuitem"],[role="option"]';
                          const isInteractive = element => element instanceof Element && element.matches(interactiveSelector);
                          const nestedInteractive = [...document.querySelectorAll(interactiveSelector)]
                            .filter(isInteractive)
                            .filter(element => {
                              for (let ancestor = element.parentElement; ancestor; ancestor = ancestor.parentElement) {
                                if (isInteractive(ancestor)) return true;
                              }
                              return false;
                            });
                          if (nestedInteractive.length) failures.push(`nested interactive elements: ${nestedInteractive.length}`);

                          return {
                            title: document.title,
                            lang,
                            h1: (h1s[0]?.innerText || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim(),
                            bodyText: doc?.innerText || '',
                            clientWidth: document.documentElement.clientWidth,
                            scrollWidth: document.documentElement.scrollWidth,
                            scrollHeight: document.documentElement.scrollHeight,
                            innerWidth: window.innerWidth,
                            devicePixelRatio: window.devicePixelRatio,
                            visualViewportWidth: window.visualViewport?.width || 0,
                            visualViewportScale: window.visualViewport?.scale || 0,
                            narrowMediaQuery: window.matchMedia('(max-width: 767px)').matches,
                            doc: Boolean(doc),
                            main: Boolean(document.querySelector('main') || document.querySelector('.VPHome')),
                            nav: Boolean(document.querySelector('.VPNav')),
                            sidebar: Boolean(document.querySelector('.VPSidebar')),
                            tables: doc?.querySelectorAll('table').length || 0,
                            codeBlocks: doc?.querySelectorAll('pre').length || 0,
                            rawAnchorText: document.body.innerText.includes('<a id='),
                            visibleDetails: [...document.querySelectorAll('details')].filter(item => item.open && visible(item)).length,
                            accessibilityFailures: failures,
                          };
                        }"""
                    )

                    page.keyboard.press("Tab")
                    focused = page.evaluate(
                        r"""() => {
                          const element = document.activeElement;
                          if (!element || element === document.body || element === document.documentElement) {
                            return { valid: false, tag: '', name: '' };
                          }
                          const name = (
                            element.getAttribute?.('aria-label') ||
                            element.getAttribute?.('title') ||
                            element.textContent ||
                            ''
                          ).replace(/\s+/g, ' ').trim();
                          return { valid: true, tag: element.tagName.toLowerCase(), name };
                        }"""
                    )
                    accessibility_failures = list(metrics["accessibilityFailures"])
                    if not bool(focused["valid"]):
                        accessibility_failures.append("Tab key did not move focus to an interactive element")

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
                    observation_positions = [("top", 0)]
                    if max_y:
                        observation_positions.extend([("middle", max_y // 2), ("bottom", max_y)])
                    screenshot_positions = {"top"}
                    if site_page.route in DECISION_CRITICAL_ROUTES:
                        screenshot_positions.update(position for position, _ in observation_positions)

                    screenshot_paths: list[str] = []
                    screenshot_dimensions: list[dict[str, object]] = []
                    overflow_observations: list[dict[str, object]] = []
                    for position, y in observation_positions:
                        page.evaluate("y => window.scrollTo(0, y)", y)
                        page.wait_for_timeout(60)
                        visible_overflow = page.evaluate(
                            r"""() => {
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
                                      ancestor.scrollWidth > ancestor.clientWidth + 1) return true;
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
                                    overflowX: style.overflowX,
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
                        if position not in screenshot_positions:
                            continue
                        target = shots / f"{route_slug(site_page.route)}-{label}-{position}.png"
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
                        if (pixel_width, pixel_height) != (expected_physical_width, expected_physical_height):
                            failures.append(
                                f"{site_page.route or '/'} / {label}: screenshot {position} is "
                                f"{pixel_width}x{pixel_height}, expected "
                                f"{expected_physical_width}x{expected_physical_height}"
                            )

                    visible_overflow_detected = any(item["offenders"] for item in overflow_observations)
                    horizontal_overflow = root_scroll_overflow or visible_overflow_detected
                    item = {
                        "renderer": "vitepress-build-playwright-full-site",
                        "source": site_page.source,
                        "route": site_page.route,
                        "generated": site_page.generated,
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
                        "lang": metrics["lang"],
                        "h1": metrics["h1"],
                        "expected_h1": site_page.heading,
                        "vp_doc": bool(metrics["doc"]),
                        "main_landmark": bool(metrics["main"]),
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
                        "keyboard_focus": focused,
                        "accessibility_failures": accessibility_failures,
                        "console_errors": console_errors,
                        "page_errors": page_errors,
                        "failed_requests": failed_requests,
                        "screenshots": screenshot_paths,
                        "screenshot_dimensions": screenshot_dimensions,
                    }
                    evidence.append(item)

                    prefix = f"{site_page.route or '/'} / {label}"
                    if status != 200:
                        failures.append(f"{prefix}: HTTP {status}")
                    if not metrics["doc"] or not metrics["nav"] or not metrics["main"]:
                        failures.append(f"{prefix}: missing VitePress document shell or landmark")
                    if str(metrics["h1"]).strip() != site_page.heading:
                        failures.append(
                            f"{prefix}: rendered H1 {metrics['h1']!r} differs from source H1 {site_page.heading!r}"
                        )
                    if not viewport_model_valid:
                        failures.append(f"{prefix}: viewport/zoom emulation is invalid")
                    if horizontal_overflow:
                        failures.append(f"{prefix}: horizontal overflow")
                    if metrics["rawAnchorText"]:
                        failures.append(f"{prefix}: raw anchor text")
                    if site_page.route == "closed_book_workbook" and int(metrics["visibleDetails"]) != 0:
                        failures.append(f"{prefix}: open solution details in closed-book page")
                    for message in accessibility_failures:
                        failures.append(f"{prefix}: accessibility: {message}")
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
            "scripts/site_inventory.py",
            "scripts/serve_built_site.py",
            "package.json",
            "package-lock.json",
            "docs/.vitepress/config.mts",
            "docs/.vitepress/theme/index.ts",
            "docs/.vitepress/theme/style.css",
        ],
    )
    payload = {
        "schema_version": "2.0",
        "source_digest": source_digest,
        "page_count": len(pages),
        "viewport_count": len(VIEWPORTS),
        "expected_case_count": len(pages) * len(VIEWPORTS),
        "cases": evidence,
        "failures": failures,
    }
    (output / "visual_evidence.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"VITEPRESS_VISUAL_SOURCE_DIGEST={source_digest}")
    print(f"VITEPRESS_VISUAL_PAGES={len(pages)}")
    print(f"VITEPRESS_VISUAL_CASES={len(evidence)}")
    print(f"VITEPRESS_VISUAL_SCREENSHOTS={sum(len(item['screenshots']) for item in evidence)}")
    print(f"VITEPRESS_VISUAL_FAILURES={len(failures)}")
    for failure in failures:
        print(f"VITEPRESS_VISUAL_FAILURE={failure}")
    print("VITEPRESS_VISUAL_RESULT=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
