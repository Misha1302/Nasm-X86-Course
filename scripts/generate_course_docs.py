#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from course_manifest import DAY_RELATIVE_PATHS, GENERATED_RELATIVE_PATHS, STANDALONE_RELATIVE_PATHS
from content_normalization import normalize_visible

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DAYS = [ROOT / rel for rel in DAY_RELATIVE_PATHS]
STANDALONE = [ROOT / rel for rel in STANDALONE_RELATIVE_PATHS]
FINGERPRINTS = ROOT / "scripts" / "answer_fingerprints.json"

missing = [str(path.relative_to(ROOT)) for path in STANDALONE if not path.is_file()]
if missing:
    raise SystemExit("Missing standalone-course sources: " + ", ".join(missing))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def source_snapshot() -> dict[str, str]:
    paths = [*STANDALONE, ROOT / "scripts" / "generate_course_docs.py", ROOT / "scripts" / "course_manifest.py", ROOT / "scripts" / "content_normalization.py", FINGERPRINTS]
    return {str(path.relative_to(ROOT)): sha256_file(path) for path in sorted(set(paths))}


def section(text: str, title: str) -> str:
    match = re.search(rf"(?m)^## {re.escape(title)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end():]
    end = re.search(r"(?m)^## ", tail)
    return tail[: end.start() if end else None].strip()


def strip_solution_blocks(text: str) -> str:
    text = re.sub(
        r"(?is)<details(?:\s[^>]*)?>.*?</details>",
        "> Решение скрыто. Зафиксируй законченную попытку и сверяйся с канонической главой позже.",
        text,
    )
    text = re.sub(
        r"(?ims)^:::\s*(?:details|solution)[^\n]*\n.*?^:::\s*$",
        "> Решение скрыто. Зафиксируй законченную попытку.",
        text,
    )
    return text


def demote_embedded_h1(text: str) -> str:
    """Demote source-page H1 headings without changing fenced examples."""
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = None
        if stripped.startswith("```"):
            marker = "```"
        elif stripped.startswith("~~~"):
            marker = "~~~"
        if marker is not None:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            output.append(line)
            continue
        if fence is None and line.startswith("# "):
            line = "#" + line
        output.append(line)
    return "\n".join(output)


def namespace_embedded_ids(text: str, source: str) -> str:
    prefix = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    ids = set(re.findall(r'id="([^"]+)"', text))
    for anchor in sorted(ids, key=len, reverse=True):
        scoped = f"{prefix}-{anchor}"
        text = text.replace(f'id="{anchor}"', f'id="{scoped}"')
        text = text.replace(f'](#{anchor})', f'](#{scoped})')
    return text


def normalize(text: str, *, strip_asm_comments: bool = True) -> str:
    if strip_asm_comments:
        text = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    return normalize_visible(text)


def validate_closed_book(text: str) -> None:
    contract = json.loads(FINGERPRINTS.read_text(encoding="utf-8"))
    low = text.lower()
    normalized = normalize(text)
    for marker in contract["solution_container_patterns"]:
        if marker.lower() in low:
            raise SystemExit(f"CLOSED-BOOK-CONTAINER: generated artifact contains {marker!r}")
    for fingerprint in contract["fingerprints"]:
        if "docs/closed_book_workbook.md" not in fingerprint.get("protected_targets", contract["protected_targets"]):
            continue
        fragment = normalize(fingerprint["fragment"], strip_asm_comments=False)
        if fragment and fragment in normalized:
            raise SystemExit(
                "CLOSED-BOOK-LEAK: "
                f"task={fingerprint['task']} id={fingerprint['id']} fragment={fingerprint['fragment'][:100]}"
            )


before = source_snapshot()

textbook_parts = [
    "# Полный самостоятельный учебник NASM x86 / IA-32",
    "",
    "> Этот файл сгенерирован из полного канонического маршрута. Не редактируй его вручную.",
    "",
    "Он включает диагностику, короткие повторения, глоссарий, 24 учебные главы, маршрут Дня 10, проверенные экзаменационные паттерны, задачи, ключи, пошаговые разборы, контрольные точки, финальный экзамен и восстановление.",
    "",
]
for path in STANDALONE:
    textbook_parts.extend(
        [
            "---",
            "",
            f"<!-- source: {path.relative_to(ROOT)} -->",
            "",
            namespace_embedded_ids(
                demote_embedded_h1(path.read_text(encoding="utf-8").strip()),
                str(path.relative_to(ROOT)),
            ),
            "",
        ]
    )
(DOCS / "textbook.md").write_text("\n".join(textbook_parts).rstrip() + "\n", encoding="utf-8")

closed = [
    "# Тетрадь NASM IA-32 без встроенных ответов",
    "",
    "> Эта страница сгенерирована автоматически. Solution containers и известные answer fingerprints запрещены.",
    "",
]
for path in DAYS:
    practice = strip_solution_blocks(section(path.read_text(encoding="utf-8"), "Практика"))
    closed.extend(
        [
            "---",
            "",
            f"<!-- source-practice: {path.relative_to(ROOT)} -->",
            "",
            f"## {path.stem.replace('_', ' ').title()}",
            "",
            practice,
            "",
        ]
    )
closed.extend(
    [
        "---",
        "",
        "<!-- source-transfer: docs/transfer_workbook.md -->",
        "",
        namespace_embedded_ids(
            demote_embedded_h1((DOCS / "transfer_workbook.md").read_text(encoding="utf-8").strip()),
            "docs/transfer_workbook.md",
        ),
        "",
        "---",
        "",
        "<!-- source-final-exam: docs/final_exam.md -->",
        "",
        namespace_embedded_ids(
            demote_embedded_h1((DOCS / "final_exam.md").read_text(encoding="utf-8").strip()),
            "docs/final_exam.md",
        ),
        "",
    ]
)
closed_text = "\n".join(closed).rstrip() + "\n"
validate_closed_book(closed_text)
(DOCS / "closed_book_workbook.md").write_text(closed_text, encoding="utf-8")

required = {"## Входные знания", "## За 30 секунд", "## Минимум после главы", "## Практика", "## Чеклист", "## Следующий шаг"}
rows: list[str] = []
for path in DAYS:
    text = path.read_text(encoding="utf-8")
    present = sorted(heading for heading in required if heading in text)
    status = "структура-6/6" if len(present) == len(required) else ("частично" if present else "нет структуры")
    rows.append(f"| [{path.stem.replace('_', ' ').title()}](/{path.stem}) | {status} | {len(present)}/6 |")

migration = [
    "# Структурный статус глав",
    "",
    "> Страница сгенерирована автоматически. `6/6` доказывает только наличие обязательных блоков, а не качество содержания.",
    "",
    "| Глава | Статус | Обязательные блоки |",
    "|---|---|---:|",
    *rows,
    "",
]
(DOCS / "course_migration.md").write_text("\n".join(migration).rstrip() + "\n", encoding="utf-8")

after = source_snapshot()
if before != after:
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    raise SystemExit("GENERATION-SOURCE-RACE: source changed during generation: " + ", ".join(changed))

generated = {}
for rel in GENERATED_RELATIVE_PATHS:
    if rel.endswith("generated_source_manifest.json"):
        continue
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"GENERATION-MISSING: {rel}")
    generated[rel] = sha256_file(path)

source_tree_sha256 = sha256_bytes(
    "".join(f"{path}\0{digest}\n" for path, digest in sorted(after.items())).encode("utf-8")
)
manifest = {
    "schema_version": "2.0",
    "source_revision": "sha256:" + source_tree_sha256,
    "source_tree_sha256": source_tree_sha256,
    "sources": after,
    "generated": generated,
}
(DOCS / "generated_source_manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(f"GENERATED_SOURCE_REVISION={manifest['source_revision']}")
print(f"GENERATED_SOURCE_TREE_SHA256={source_tree_sha256}")
print(f"GENERATED_FILES={len(generated) + 1}")
print("GENERATED_DOCS=PASS")
