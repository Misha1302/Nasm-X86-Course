#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_provenance import digest_paths
from playwright.sync_api import ConsoleMessage, Error, Request, sync_playwright
from render_vitepress_pages import VIEWPORTS, page_url, route_slug
from site_inventory import discover_site_pages

ROOT = Path(__file__).resolve().parents[1]


def source_has_rendered_details(text: str) -> bool:
    """Find block-level disclosure syntax outside fenced examples."""
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else ("~~~" if stripped.startswith("~~~") else None)
        if marker is not None:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue
        lowered = stripped.lower()
        if lowered.startswith("::: details") or lowered.startswith("<details"):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open every rendered disclosure and audit its expanded visual state."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument(
        "--output",
        default=str(ROOT / "render-evidence" / "vitepress" / "expanded-details"),
    )
    ns = parser.parse_args()

    pages = tuple(
        page
        for page in discover_site_pages()
        if source_has_rendered_details((ROOT / page.source).read_text(encoding="utf-8"))
    )
    output = Path(ns.output).resolve()
    shots = output / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    for old in shots.glob("*.png"):
        old.unlink()

    cases: list[dict[str, object]] = []
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
                        failed_requests.append(f"{request.method} {request.url}: {request.failure}")

                    page.on("console", on_console)
                    page.on("pageerror", on_page_error)
                    page.on("requestfailed", on_request_failed)

                    url = page_url(ns.base_url, site_page)
                    response = page.goto(url, wait_until="networkidle")
                    status = response.status if response else 0
                    state = page.evaluate(
                        """() => {
                          const details = [...document.querySelectorAll('.VPDoc details')];
                          for (const item of details) item.open = true;
                          return { total: details.length, open: details.filter(item => item.open).length };
                        }"""
                    )
                    page.wait_for_timeout(100)

                    scroll_height = int(page.evaluate("() => document.documentElement.scrollHeight"))
                    max_y = max(0, scroll_height - height)
                    positions = [("top", 0)]
                    if max_y:
                        positions.extend([("middle", max_y // 2), ("bottom", max_y)])

                    observations: list[dict[str, object]] = []
                    for position, y in positions:
                        page.evaluate("y => window.scrollTo(0, y)", y)
                        page.wait_for_timeout(60)
                        observed = page.evaluate(
                            """() => {
                              const viewportWidth = window.visualViewport?.width || window.innerWidth;
                              const viewportHeight = window.visualViewport?.height || window.innerHeight;
                              const insideHorizontalScroller = element => {
                                for (let ancestor = element.parentElement; ancestor; ancestor = ancestor.parentElement) {
                                  const style = getComputedStyle(ancestor);
                                  if ((style.overflowX === 'auto' || style.overflowX === 'scroll') &&
                                      ancestor.scrollWidth > ancestor.clientWidth + 1) return true;
                                }
                                return false;
                              };
                              const selector = element => {
                                if (element.id) return `${element.tagName.toLowerCase()}#${element.id}`;
                                const classes = [...element.classList].slice(0, 3).join('.');
                                return element.tagName.toLowerCase() + (classes ? `.${classes}` : '');
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
                                  });
                                  if (offenders.length >= 20) break;
                                }
                              }
                              return {
                                viewportWidth,
                                viewportHeight,
                                rootOverflow: document.documentElement.scrollWidth >
                                  document.documentElement.clientWidth + 1,
                                offenders,
                              };
                            }"""
                        )
                        observations.append(
                            {
                                "position": position,
                                "scroll_y": y,
                                "root_overflow": bool(observed["rootOverflow"]),
                                "offenders": observed["offenders"],
                            }
                        )

                    screenshot = shots / f"{route_slug(site_page.route)}-{label}-expanded-top.png"
                    page.evaluate("() => window.scrollTo(0, 0)")
                    page.screenshot(path=str(screenshot), full_page=False, animations="disabled")

                    case_failures: list[str] = []
                    if status != 200:
                        case_failures.append(f"HTTP {status}")
                    if int(state["total"]) == 0:
                        case_failures.append("source contains disclosure syntax but rendered page has no details")
                    if int(state["open"]) != int(state["total"]):
                        case_failures.append(f"only {state['open']} of {state['total']} details opened")
                    if any(item["root_overflow"] or item["offenders"] for item in observations):
                        case_failures.append("horizontal overflow with all details expanded")
                    case_failures.extend(f"console error: {message}" for message in console_errors)
                    case_failures.extend(f"page error: {message}" for message in page_errors)
                    case_failures.extend(f"request failed: {message}" for message in failed_requests)

                    prefix = f"{site_page.route or '/'} / {label}"
                    failures.extend(f"{prefix}: {message}" for message in case_failures)
                    cases.append(
                        {
                            "source": site_page.source,
                            "route": site_page.route,
                            "viewport": label,
                            "http_status": status,
                            "details_total": int(state["total"]),
                            "details_open": int(state["open"]),
                            "observations": observations,
                            "screenshot": str(screenshot.relative_to(output)),
                            "failures": case_failures,
                        }
                    )
                    context.close()
        finally:
            browser.close()

    source_digest = digest_paths(
        ROOT,
        [
            "scripts/audit_expanded_details.py",
            "scripts/render_vitepress_pages.py",
            "scripts/site_inventory.py",
            "docs/.vitepress/config.mts",
            "docs/.vitepress/theme/style.css",
        ],
    )
    payload = {
        "schema_version": "1.0",
        "source_digest": source_digest,
        "page_count": len(pages),
        "viewport_count": len(VIEWPORTS),
        "expected_case_count": len(pages) * len(VIEWPORTS),
        "cases": cases,
        "failures": failures,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "expanded_details_evidence.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"EXPANDED_DETAILS_PAGES={len(pages)}")
    print(f"EXPANDED_DETAILS_CASES={len(cases)}")
    print(f"EXPANDED_DETAILS_FAILURES={len(failures)}")
    for failure in failures:
        print(f"EXPANDED_DETAILS_FAILURE={failure}")
    print("EXPANDED_DETAILS_RESULT=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
