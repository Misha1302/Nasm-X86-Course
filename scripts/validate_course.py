#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
errors: list[str] = []

for i in range(1, 26):
    path = DOCS / f"day_{i:02d}.md"
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")

for generated in (DOCS / "textbook.md", DOCS / "course_migration.md"):
    if not generated.is_file() or "сгенерирован" not in generated.read_text(encoding="utf-8").lower():
        errors.append(f"generated document is absent or lacks marker: {generated.relative_to(ROOT)}")

if (DOCS / "fpu_double_site_page.md").exists():
    errors.append("duplicate owner docs/fpu_double_site_page.md must not exist")

lock = (ROOT / "package-lock.json").read_text(encoding="utf-8")
if "applied-caas-gateway" in lock or "internal.api.openai.org" in lock:
    errors.append("package-lock.json contains a private registry URL")

asm_stems = {p.stem for p in (ROOT / "examples").glob("*.asm")}
expected_stems = {p.stem for p in (ROOT / "examples" / "expected").glob("*.txt")}
if asm_stems != expected_stems:
    errors.append(f"example/expected mismatch: asm={sorted(asm_stems)}, expected={sorted(expected_stems)}")

for path in (ROOT / "examples").glob("*.asm"):
    if ".note.GNU-stack" not in path.read_text(encoding="utf-8"):
        errors.append(f"missing non-executable-stack marker: {path.relative_to(ROOT)}")

required_markers = {
    "docs/day_25.md": ["uint32_t mask = 0u - (ux >> 31);", "INT32_MIN"],
    "docs/day_10.md": ["может переполниться", "INT32_MIN"],
    "docs/patterns/branchless.md": ["INT32_MIN"],
    "docs/tasks/spring-01/01-14-garden.md": ["может переполниться"],
}
for rel, markers in required_markers.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"missing technical boundary {marker!r} in {rel}")

config = (DOCS / ".vitepress" / "config.mts").read_text(encoding="utf-8")
for link in re.findall(r'link:\s*"(/[^"]+)"', config):
    if link == "/":
        continue
    candidate = DOCS / (link.removeprefix("/") + ".md")
    index_candidate = DOCS / link.removeprefix("/") / "index.md"
    if not candidate.exists() and not index_candidate.exists():
        errors.append(f"broken sidebar/nav link: {link}")

if errors:
    raise SystemExit("Course validation failed:\n- " + "\n- ".join(errors))
print("Course validation passed")
