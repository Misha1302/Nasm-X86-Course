#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DAYS = [DOCS / f"day_{i:02d}.md" for i in range(1, 26)]

STANDALONE_SECTIONS = [
    DOCS / "self_study.md",
    *DAYS[:10],
    DOCS / "day_10_learning_path.md",
    *DAYS[10:],
    DOCS / "transfer_workbook.md",
    DOCS / "transfer_keys.md",
    DOCS / "checkpoints.md",
    DOCS / "checkpoint_keys.md",
    DOCS / "ai_tutor_prompts.md",
    DOCS / "ai_tutor_eval.md",
]

missing = [str(path.relative_to(ROOT)) for path in STANDALONE_SECTIONS if not path.is_file()]
if missing:
    raise SystemExit("Missing standalone-course sources: " + ", ".join(missing))

parts = [
    "# Полный самостоятельный учебник NASM x86 / IA-32",
    "",
    "> Этот файл сгенерирован из канонических страниц курса. Не редактируй его вручную.",
    "",
    "Он включает самостоятельный маршрут, все 25 глав, отдельный маршрут Дня 10, transfer-задачи, диагностические ключи, checkpoints, рубрики и AI-наставника.",
    "",
]
for path in STANDALONE_SECTIONS:
    parts.extend(
        [
            "---",
            "",
            f"<!-- source: {path.relative_to(ROOT)} -->",
            "",
            path.read_text(encoding="utf-8").strip(),
            "",
        ]
    )
(DOCS / "textbook.md").write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")

required = {"## Входные знания", "## За 30 секунд", "## Минимум после главы", "## Практика", "## Чеклист", "## Следующий шаг"}
rows = []
for path in DAYS:
    text = path.read_text(encoding="utf-8")
    present = sorted(heading for heading in required if heading in text)
    if len(present) == len(required):
        status = "standalone"
    elif present:
        status = "transitional"
    else:
        status = "legacy"
    rows.append(f"| [{path.stem.replace('_', ' ').title()}](/{path.stem}) | {status} | {len(present)}/6 |")

migration = [
    "# Статус самостоятельности глав",
    "",
    "> Страница сгенерирована автоматически. Канонические источники — `day_01.md` … `day_25.md`.",
    "",
    "Каждая глава обязана иметь структурный каркас и явный переход в рабочую тетрадь. Статус не оценивает качество объяснения сам по себе, но ловит структурную регрессию.",
    "",
    "| Глава | Статус | Обязательные блоки |",
    "|---|---|---:|",
    *rows,
    "",
    "`standalone` означает наличие всех шести обязательных блоков. `transitional` и `legacy` должны отклоняться CI.",
]
(DOCS / "course_migration.md").write_text("\n".join(migration).rstrip() + "\n", encoding="utf-8")
