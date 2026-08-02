#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

from course_manifest import DAY_RELATIVE_PATHS, STANDALONE_RELATIVE_PATHS

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DAYS = [ROOT / rel for rel in DAY_RELATIVE_PATHS]
STANDALONE = [ROOT / rel for rel in STANDALONE_RELATIVE_PATHS]

missing = [str(path.relative_to(ROOT)) for path in STANDALONE if not path.is_file()]
if missing:
    raise SystemExit("Missing standalone-course sources: " + ", ".join(missing))


def section(text: str, title: str) -> str:
    match = re.search(rf"(?m)^## {re.escape(title)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end():]
    end = re.search(r"(?m)^## ", tail)
    return tail[: end.start() if end else None].strip()


def strip_solution_blocks(text: str) -> str:
    # Closed-book output hides every HTML details block regardless of its visible
    # summary (Ответ, Один вариант, Подсказка...). The semantic boundary is the
    # details element, not a Russian label that can drift.
    text = re.sub(
        r"(?is)<details(?:\s[^>]*)?>.*?</details>",
        "> Решение скрыто. Зафиксируй законченную попытку и сверяйся с канонической главой позже.",
        text,
    )
    # Also hide VitePress details containers if they are introduced later.
    text = re.sub(
        r"(?ims)^:::\s*details[^\n]*\n.*?^:::\s*$",
        "> Решение скрыто. Зафиксируй законченную попытку.",
        text,
    )
    return text


textbook_parts = [
    "# Полный самостоятельный учебник NASM x86 / IA-32",
    "",
    "> Этот файл сгенерирован из полного канонического маршрута. Не редактируй его вручную.",
    "",
    "Он включает диагностику, короткие повторения, глоссарий, 24 учебные главы, маршрут Дня 10, задачи, ключи, пошаговые разборы, контрольные точки, финальный экзамен и восстановление.",
    "",
]
for path in STANDALONE:
    textbook_parts.extend(
        [
            "---",
            "",
            f"<!-- source: {path.relative_to(ROOT)} -->",
            "",
            path.read_text(encoding="utf-8").strip(),
            "",
        ]
    )
(DOCS / "textbook.md").write_text("\n".join(textbook_parts).rstrip() + "\n", encoding="utf-8")

closed = [
    "# Тетрадь NASM IA-32 без встроенных ответов",
    "",
    "> Эта страница сгенерирована автоматически. Все раскрывающиеся решения удалены независимо от подписи блока.",
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
        (DOCS / "transfer_workbook.md").read_text(encoding="utf-8").strip(),
        "",
        "---",
        "",
        "<!-- source-final-exam: docs/final_exam.md -->",
        "",
        (DOCS / "final_exam.md").read_text(encoding="utf-8").strip(),
        "",
    ]
)
(DOCS / "closed_book_workbook.md").write_text("\n".join(closed).rstrip() + "\n", encoding="utf-8")

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
