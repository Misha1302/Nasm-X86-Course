#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DAYS = [DOCS / f"day_{i:02d}.md" for i in range(1, 26)]

missing = [str(path.relative_to(ROOT)) for path in DAYS if not path.is_file()]
if missing:
    raise SystemExit("Missing course days: " + ", ".join(missing))

parts = [
    "# Полный учебник NASM x86 / IA-32",
    "",
    "> Этот файл сгенерирован из `docs/day_01.md` … `docs/day_25.md`. Не редактируй его вручную.",
    "",
]
for path in DAYS:
    parts.extend(["---", "", path.read_text(encoding="utf-8").strip(), ""])
(DOCS / "textbook.md").write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")

required = {"## За 30 секунд", "## Минимум после главы", "## Практика", "## Чеклист"}
rows = []
for path in DAYS:
    text = path.read_text(encoding="utf-8")
    present = sorted(heading for heading in required if heading in text)
    if len(present) == len(required):
        status = "structured"
    elif present:
        status = "transitional"
    else:
        status = "legacy"
    rows.append(f"| [{path.stem.replace('_', ' ').title()}](/{path.stem}) | {status} | {len(present)}/4 |")

migration = [
    "# Статус миграции глав",
    "",
    "> Страница сгенерирована автоматически. Канонические источники — `day_01.md` … `day_25.md`.",
    "",
    "Новые и существенно переработанные главы обязаны следовать `course_style.md`. Старые главы остаются валидными, но их переход к единому формату виден явно и не скрывается.",
    "",
    "| Глава | Статус | Блоки нового шаблона |",
    "|---|---|---:|",
    *rows,
    "",
    "Статусы: `structured` — полный новый шаблон; `transitional` — часть блоков внедрена; `legacy` — глава ещё использует прежний каркас.",
]
(DOCS / "course_migration.md").write_text("\n".join(migration).rstrip() + "\n", encoding="utf-8")
