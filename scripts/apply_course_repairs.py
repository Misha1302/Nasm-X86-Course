#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = os.environ.get("GITHUB_REF_NAME", "fix/course-quality-20260726-impl")


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, got {count}: {old[:80]!r}")
    write(path, content.replace(old, new, 1))


# Reproducible Node dependency contract.
package = json.loads(read("package.json"))
package["scripts"] = {
    "docs:generate": "python3 scripts/generate_course_docs.py",
    "course:validate": "python3 scripts/validate_course.py",
    "docs:dev": "npm run docs:generate && vitepress dev docs --host 0.0.0.0",
    "docs:build": "npm run docs:generate && npm run course:validate && vitepress build docs",
    "docs:preview": "vitepress preview docs --host 0.0.0.0",
    "docs:clean": "rm -rf docs/.vitepress/cache docs/.vitepress/dist docs/textbook.md docs/course_migration.md",
}
package["devDependencies"] = {"vitepress": "1.6.4"}
write("package.json", json.dumps(package, ensure_ascii=False, indent=2))

# Generated documents remove manually maintained duplicate owners.
write(
    "scripts/generate_course_docs.py",
    '''#!/usr/bin/env python3
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
(DOCS / "textbook.md").write_text("\\n".join(parts).rstrip() + "\\n", encoding="utf-8")

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
(DOCS / "course_migration.md").write_text("\\n".join(migration).rstrip() + "\\n", encoding="utf-8")
''',
)

write(
    "scripts/validate_course.py",
    '''#!/usr/bin/env python3
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
''',
)

# Validation and deployment workflows.
write(
    ".github/workflows/validate-course.yml",
    '''name: Validate course

on:
  push:
  pull_request:
  workflow_dispatch:

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies from lock file
        run: npm ci --no-audit --no-fund

      - name: Generate and validate course documents
        run: |
          npm run docs:generate
          npm run course:validate

      - name: Build VitePress site
        run: npm run docs:build

  asm-examples:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install NASM and 32-bit toolchain
        run: |
          sudo apt-get update
          sudo apt-get install -y nasm gcc-multilib libc6-dev-i386

      - name: Build and verify examples
        run: |
          set -euo pipefail
          for file in examples/*.asm; do
            name="$(basename "$file" .asm)"
            nasm -f elf32 -g -F dwarf "$file" -o "/tmp/$name.o"
            gcc -m32 -g -no-pie -Wl,-z,noexecstack "/tmp/$name.o" -o "/tmp/$name"
            "/tmp/$name" > "/tmp/$name.out"
            diff -u "examples/expected/$name.txt" "/tmp/$name.out"
          done
''',
)

write(
    ".github/workflows/deploy-docs.yml",
    '''name: Deploy VitePress site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies from lock file
        run: npm ci --no-audit --no-fund

      - name: Build VitePress site
        run: npm run docs:build

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/.vitepress/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
''',
)

# Golden outputs and executable-stack metadata.
expected = {
    "01_minimal": "",
    "02_pack_bytes": "168496141\n",
    "03_masked_merge": "2863289685\n",
    "04_branchless_abs": "123\n",
    "05_pandora_year": "125\n",
    "06_signed_division": "-3 -2\n",
    "07_jump_table": "30\n",
    "08_x87_printf": "5.000000\n",
}
for stem, output in expected.items():
    write(f"examples/expected/{stem}.txt", output)
for path in sorted((ROOT / "examples").glob("*.asm")):
    text = path.read_text(encoding="utf-8").rstrip()
    if ".note.GNU-stack" not in text:
        text += "\n\nsection .note.GNU-stack noalloc noexec nowrite progbits"
    path.write_text(text + "\n", encoding="utf-8")

# Technical correctness boundaries.
replace_once(
    "docs/day_25.md",
    """```cpp
mask = x >> 31;
ans = (x ^ mask) - mask;
```""",
    """```cpp
uint32_t ux = static_cast<uint32_t>(x);
uint32_t mask = 0u - (ux >> 31);
uint32_t ans = (ux ^ mask) - mask;
```

Так C++-запись точно воспроизводит 32-битную маску `0/FFFFFFFFh`, которую в NASM даёт `sar reg, 31`. Для `INT32_MIN` битовый результат равен `0x80000000`, но положительное значение `2147483648` не помещается в `int32_t`; это нужно учитывать в условии задачи и формате вывода.""",
)

replace_once(
    "docs/day_10.md",
    """```asm
mov eax, [a]
add eax, [b]
dec eax
xor edx, edx
div dword [b]
; eax = ceil(a / b)
```""",
    """```asm
mov eax, [a]
add eax, [b]
dec eax
xor edx, edx
div dword [b]
; eax = ceil(a / b)
```

::: warning Граница формулы
Формула `(a + b - 1) / b` корректна только когда промежуточное `a + b - 1` помещается в 32 бита. Если ограничения этого не гарантируют, считай `a / b` и отдельно прибавляй `1`, когда остаток ненулевой.
:::""",
)

replace_once(
    "docs/day_10.md",
    "Подробнее: [Branchless-маски](/patterns/branchless).",
    "Подробнее: [Branchless-маски](/patterns/branchless).\n\nДля `INT32_MIN` обычный положительный `abs` не помещается в signed 32-bit. В задачах нужно заранее определить, ожидается ли битовый результат `0x80000000`, более широкий тип или исключение этого входа ограничениями.",
)

for rel, section in {
    "docs/patterns/branchless.md": """## Граница branchless `abs`

Формула с маской сохраняет 32-битный битовый результат. Для `INT32_MIN` получается `0x80000000`, но положительное `2147483648` не представимо как `int32_t`. Проверяй ограничения и требуемый тип вывода.""",
    "docs/tasks/spring-01/01-14-garden.md": """## Граница округления вверх

Формула `(a + b - 1) / b` может переполниться на сложении. Используй её только когда ограничения гарантируют вместимость промежуточного результата; иначе применяй `a / b + (a % b != 0)`.""",
}.items():
    text = read(rel).rstrip()
    heading = section.splitlines()[0]
    if heading not in text:
        write(rel, text + "\n\n---\n\n" + section)

# Canonical ownership and generated-document policy.
for rel in ("docs/textbook.md", "docs/fpu_double_site_page.md"):
    path = ROOT / rel
    if path.exists():
        path.unlink()
ignore = read(".gitignore").rstrip()
for item in ("docs/textbook.md", "docs/course_migration.md"):
    if item not in ignore.splitlines():
        ignore += "\n" + item
write(".gitignore", ignore)

replace_once(
    "docs/course_style.md",
    "Эта страница — внутренний стандарт курса. Она нужна, чтобы главы были не литературным рассказом, а удобным учебным модулем.",
    "Эта страница — внутренний стандарт курса. Она нужна, чтобы главы были не литературным рассказом, а удобным учебным модулем.\n\nНовые и существенно переработанные главы обязаны следовать этому стандарту. Текущий переход старых глав отслеживается автоматически на странице [Статус миграции](/course_migration), поэтому неполная миграция не маскируется под завершённую.",
)

# New practical pages.
write(
    "docs/debugging_with_gdb.md",
    '''# Отладка NASM в GDB

## За 30 секунд

- Собирай NASM с `-g -F dwarf`, а линковку — с `-g`.
- `start` останавливается около входа в `main`.
- `layout asm` показывает инструкции, `layout regs` — регистры.
- `si` делает один машинный шаг, `ni` проходит вызов целиком.
- `x/16wx $esp` показывает 16 dword на стеке.
- После каждой инструкции сравни ожидаемое состояние с фактическим.

## Сборка для отладки

```bash
nasm -f elf32 -g -F dwarf main.asm -o main.o
gcc -m32 -g -no-pie -Wl,-z,noexecstack main.o -o main
gdb ./main
```

## Минимальный сеанс

```gdb
set disassembly-flavor intel
start
layout asm
layout regs
si
info registers eax ebx ecx edx esp ebp eflags
x/16wx $esp
```

## Как проверять стек вызова

Перед `call` запиши ожидаемые аргументы и `esp`. После возврата проверь, что CDECL-аргументы удалены правильным `add esp, N`.

```gdb
p/x $esp
x/12wx $esp
si
```

## Как ловить повреждение памяти

```gdb
break main
watch x
run
continue
```

Для адресной ошибки остановись перед подозрительной инструкцией и отдельно вычисли базу, индекс, scale и displacement.

## Практика

1. Пройди `examples/06_signed_division.asm` по одной инструкции и проверь `edx:eax` до и после `idiv`.
2. В `examples/07_jump_table.asm` посмотри адрес выбранного элемента таблицы.
3. В `examples/08_x87_printf.asm` используй `info float`, чтобы увидеть x87-стек.

## Чеклист

- [ ] Я умею собрать файл с DWARF-символами.
- [ ] Я вижу регистры и стек до/после инструкции.
- [ ] Я отличаю `si` от `ni`.
- [ ] Я проверяю вычисленный адрес, а не только итоговое падение.
''',
)

write(
    "docs/support_matrix.md",
    '''# Поддерживаемые среды

Каноническая модель курса — Linux x86-64 с установленной 32-битной toolchain, которая собирает IA-32 ELF.

| Среда | Статус | Комментарий |
|---|---|---|
| Ubuntu 24.04 x86-64 | основной сценарий | используется в CI; нужны NASM, GCC multilib и 32-битные libc headers |
| Debian x86-64 | поддерживается | названия пакетов близки к Ubuntu, но проверяй текущий релиз |
| Fedora x86-64 | поддерживается вручную | нужны 32-битные glibc development-пакеты; названия зависят от версии |
| WSL2 с Ubuntu | поддерживается | используй те же команды, что и в Ubuntu |
| macOS | через Linux VM/container | Mach-O и системный ABI отличаются от учебного ELF/CDECL |
| Windows без WSL | ограниченно | SASM подходит для первых упражнений; эталонная CLI-сборка остаётся Linux |

## Эталонная проверка

```bash
nasm -v
gcc -m32 -x c -o /tmp/hello32 - <<'C'
int main(void) { return 0; }
C
file /tmp/hello32
/tmp/hello32
```

Успех означает, что assembler, linker и 32-битная libc работают вместе. Если эта проверка не проходит, сначала исправь среду, а не NASM-код задачи.
''',
)

write(
    "docs/modern_x86_64_next.md",
    '''# Что изучать после IA-32

Этот курс намеренно использует IA-32, потому что домашки и экзаменационная модель построены вокруг `eax`, `esp`, `ebp`, стековых аргументов и CDECL.

После курса переходи к современному x86-64 отдельным треком, не смешивая ABI:

1. регистры `rax` … `r15` и частичные регистры;
2. System V AMD64 ABI в Linux: аргументы преимущественно в регистрах;
3. 16-байтовое выравнивание стека;
4. RIP-relative addressing, PIE и PIC;
5. SSE2 как базовая модель scalar floating point вместо учебного x87;
6. чтение оптимизированного вывода компилятора;
7. SIMD, AVX и измерение производительности только после профилирования.

IA-32 здесь — учебная и экзаменационная модель. Она помогает понять стек и ABI, но не должна автоматически переноситься на современный 64-битный код.
''',
)

# Navigation and landing pages.
config = read("docs/.vitepress/config.mts")
config = config.replace(
    '{ text: "Ошибки", link: "/debug_cards" },\n            { text: "C ABI", link: "/c_abi" },',
    '{ text: "Ошибки", link: "/debug_cards" },\n            { text: "GDB", link: "/debugging_with_gdb" },\n            { text: "C ABI", link: "/c_abi" },',
)
config = config.replace(
    '{ text: "Карточки ошибок", link: "/debug_cards" },\n                    { text: "Стиль глав курса", link: "/course_style" }',
    '{ text: "Карточки ошибок", link: "/debug_cards" },\n                    { text: "Отладка в GDB", link: "/debugging_with_gdb" },\n                    { text: "Поддерживаемые среды", link: "/support_matrix" },\n                    { text: "Статус миграции", link: "/course_migration" },\n                    { text: "Стиль глав курса", link: "/course_style" }',
)
config = config.replace(
    '{ text: "День 25 — mock exam", link: "/day_25" }',
    '{ text: "День 25 — mock exam", link: "/day_25" },\n                    { text: "После IA-32: x86-64", link: "/modern_x86_64_next" }',
)
write("docs/.vitepress/config.mts", config)

index = read("docs/index.md")
index = index.replace(
    "| Быстро найти типовую ошибку | [Карточки ошибок](/debug_cards) |",
    "| Быстро найти типовую ошибку | [Карточки ошибок](/debug_cards) |\n| Пошагово проверить регистры и стек | [Отладка в GDB](/debugging_with_gdb) |\n| Проверить совместимость среды | [Поддерживаемые среды](/support_matrix) |",
)
index = index.replace(
    "- Дни 20–25: запуск программы, безопасность, floating point, x87, C++ object model и mock exam.",
    "- Дни 20–25: запуск программы, безопасность, floating point, x87, C++ object model и mock exam.\n- После экзамена: [отдельный маршрут x86-64](/modern_x86_64_next), чтобы не смешивать IA-32 CDECL с современным ABI.",
)
write("docs/index.md", index)

readme = read("README.md")
readme = readme.replace(
    "| [`docs/debug_cards.md`](docs/debug_cards.md) | быстрый справочник типовых ошибок |",
    "| [`docs/debug_cards.md`](docs/debug_cards.md) | быстрый справочник типовых ошибок |\n| [`docs/debugging_with_gdb.md`](docs/debugging_with_gdb.md) | пошаговая отладка регистров, памяти и стека |\n| [`docs/support_matrix.md`](docs/support_matrix.md) | проверяемая матрица учебных сред |\n| [`docs/modern_x86_64_next.md`](docs/modern_x86_64_next.md) | следующий трек после экзаменационного IA-32 |",
)
write("README.md", readme)

# Regenerate public lock file and run all relevant checks before committing.
lock = ROOT / "package-lock.json"
if lock.exists():
    lock.unlink()
run("npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org/")
run("npm", "ci", "--no-audit", "--no-fund")
run("npm", "run", "docs:build")

for asm in sorted((ROOT / "examples").glob("*.asm")):
    stem = asm.stem
    obj = Path("/tmp") / f"{stem}.o"
    exe = Path("/tmp") / stem
    out = Path("/tmp") / f"{stem}.out"
    run("nasm", "-f", "elf32", "-g", "-F", "dwarf", str(asm), "-o", str(obj))
    run("gcc", "-m32", "-g", "-no-pie", "-Wl,-z,noexecstack", str(obj), "-o", str(exe))
    with out.open("wb") as stream:
        subprocess.run([str(exe)], cwd=ROOT, check=True, stdout=stream)
    if out.read_bytes() != (ROOT / "examples" / "expected" / f"{stem}.txt").read_bytes():
        raise RuntimeError(f"Unexpected output for {stem}")

# Remove one-shot machinery from the resulting change set.
for rel in ("scripts/apply_course_repairs.py", ".github/workflows/one-shot-course-repair.yml"):
    path = ROOT / rel
    if path.exists():
        path.unlink()

run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "add", "-A")
run("git", "commit", "-m", "fix: harden NASM course content and validation")
run("git", "push", "origin", f"HEAD:{BRANCH}")

# Clean accidental intermediate branches created during orchestration.
for stale in (
    "fix/course-quality-20260726",
    "fix/course-quality-20260726-repair",
    "fix/course-quality-20260726-final",
    "fix/course-quality-20260726-work",
):
    subprocess.run(["git", "push", "origin", "--delete", stale], cwd=ROOT, check=False)
