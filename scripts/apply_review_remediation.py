#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == 'scripts' else Path.cwd()
DOCS = ROOT / 'docs'

changed: list[str] = []


def write(path: Path, text: str) -> None:
    old = path.read_text(encoding='utf-8') if path.exists() else None
    if old != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        changed.append(str(path.relative_to(ROOT)))


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one occurrence, found {count}')
    return text.replace(old, new, 1)


def insert_before(text: str, marker: str, block: str, *, label: str) -> str:
    if block.strip() in text:
        return text
    pos = text.find(marker)
    if pos < 0:
        raise RuntimeError(f'{label}: marker not found: {marker!r}')
    return text[:pos] + block.rstrip() + '\n\n' + text[pos:]


def align_external_calls(text: str) -> tuple[str, int]:
    """Align complete two/three-argument printf/scanf call shapes.

    Precondition documented by the course: the surrounding body starts with
    esp % 16 == 0 after the aligned main/function prologue.
    """
    total = 0

    x87 = re.compile(
        r'(?P<i>^[ \t]*)sub esp, 8\n'
        r'(?P=i)fstp qword \[esp\]\n'
        r'(?P=i)push (?P<fmt>[^\n]+)\n'
        r'(?P=i)call printf\n'
        r'(?P=i)add esp, 12',
        flags=re.M,
    )
    text, n = x87.subn(
        lambda m: (
            f"{m.group('i')}sub esp, 12      ; 4 bytes padding + 8-byte double\n"
            f"{m.group('i')}fstp qword [esp + 4]\n"
            f"{m.group('i')}push {m.group('fmt')}\n"
            f"{m.group('i')}call printf\n"
            f"{m.group('i')}add esp, 16"
        ),
        text,
    )
    total += n

    three = re.compile(
        r'(?P<i>^[ \t]*)(?P<a>push [^\n]+\n)'
        r'(?P=i)(?P<b>push [^\n]+\n)'
        r'(?P=i)(?P<c>push [^\n]+\n)'
        r'(?P=i)call (?P<fn>printf|scanf)\n'
        r'(?P=i)add esp, 12',
        flags=re.M,
    )
    text, n = three.subn(
        lambda m: (
            f"{m.group('i')}sub esp, 4       ; padding: 4 + 12 argument bytes = 16\n"
            f"{m.group('i')}{m.group('a')}"
            f"{m.group('i')}{m.group('b')}"
            f"{m.group('i')}{m.group('c')}"
            f"{m.group('i')}call {m.group('fn')}\n"
            f"{m.group('i')}add esp, 16"
        ),
        text,
    )
    total += n

    two = re.compile(
        r'(?P<i>^[ \t]*)(?P<a>push [^\n]+\n)'
        r'(?P=i)(?P<b>push [^\n]+\n)'
        r'(?P=i)call (?P<fn>printf|scanf)\n'
        r'(?P=i)add esp, 8',
        flags=re.M,
    )
    text, n = two.subn(
        lambda m: (
            f"{m.group('i')}sub esp, 8       ; padding: 8 + 8 argument bytes = 16\n"
            f"{m.group('i')}{m.group('a')}"
            f"{m.group('i')}{m.group('b')}"
            f"{m.group('i')}call {m.group('fn')}\n"
            f"{m.group('i')}add esp, 16"
        ),
        text,
    )
    total += n
    return text, total


def ensure_alignment_note(text: str) -> str:
    marker = 'Перед первым полным фрагментом с `printf`/`scanf`'
    if marker in text:
        return text
    m = re.search(r'^# .+?\n', text, flags=re.M)
    if not m:
        return text
    note = (
        '\n> **ABI-условие для libc.** Перед первым полным фрагментом с `printf`/`scanf` '
        'тело функции должно получить `esp % 16 == 0`, например через '
        '`push ebp; mov ebp, esp; and esp, -16`. Padding и аргументы вместе занимают '
        'кратное 16 число байт; полный вывод находится в [C ABI / CDECL](/c_abi) и '
        '[паттерне выравнивания](/patterns/libc_alignment).\n'
    )
    return text[:m.end()] + note + text[m.end():]


def patch_markdown_calls() -> None:
    for path in DOCS.rglob('*.md'):
        if path.name in {'textbook.md', 'course_migration.md', 'closed_book_workbook.md'}:
            continue
        text = path.read_text(encoding='utf-8')
        new, count = align_external_calls(text)
        if count:
            new = ensure_alignment_note(new)
            write(path, new)


def patch_examples() -> None:
    for path in sorted((ROOT / 'examples').glob('*.asm')):
        text = path.read_text(encoding='utf-8')
        if not re.search(r'(?m)^\s*call\s+(?:printf|scanf)\s*$', text):
            continue
        if 'and esp, -16' not in text:
            text = replace_once(
                text,
                'main:\n',
                'main:\n    push ebp\n    mov ebp, esp\n    and esp, -16\n',
                label=f'{path}: aligned main prologue',
            )
        text, count = align_external_calls(text)
        if count == 0:
            raise RuntimeError(f'{path}: no supported libc call shape was aligned')
        epilogue = '    mov esp, ebp\n    pop ebp\n    xor eax, eax\n    ret'
        if epilogue not in text:
            needle = '    xor eax, eax\n    ret'
            if needle not in text:
                raise RuntimeError(f'{path}: canonical return not found')
            head, tail = text.rsplit(needle, 1)
            text = head + epilogue + tail
        write(path, text)


def patch_alignment_docs() -> None:
    path = DOCS / 'patterns' / 'libc_alignment.md'
    write(path, '''# Паттерн: libc и 16-byte stack alignment

## Когда нужен

Этот контракт нужен для **каждого** вызова функции, собранной современной GNU/Linux i386 toolchain, а не только для Spring-04. GCC по умолчанию поддерживает 16-байтовую preferred stack boundary; смешивание старого 4-byte кода с системной libc требует явного realignment.

## Инвариант call site

Непосредственно перед `call`:

```text
esp % 16 == 0
```

После возврата caller обязан восстановить `esp` точно к состоянию до подготовки padding и аргументов.

## Выровненное тело `main`

Для учебного `main`, который возвращается через `ret`, используем простой frame:

```asm
main:
    push ebp
    mov ebp, esp
    and esp, -16

    ; body: esp % 16 == 0

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret
```

`ebp` сохраняет исходную вершину frame, поэтому эпилог восстанавливает return address независимо от того, сколько байт отбросил `and esp, -16`.

## Padding как формула

Если body начинается с `esp % 16 == 0`, то:

```text
padding = (16 - (argument_bytes % 16)) % 16
```

Padding кладётся **до** аргументов. После вызова caller убирает `padding + argument_bytes`.

| Аргументы | Bytes | Padding | Cleanup |
|---|---:|---:|---:|
| один 32-bit | 4 | 12 | 16 |
| два 32-bit | 8 | 8 | 16 |
| три 32-bit | 12 | 4 | 16 |
| четыре 32-bit | 16 | 0 | 16 |
| format pointer + `double` | 12 | 4 | 16 |

## Пример: `printf("%d\\n", x)`

```asm
sub esp, 8
push dword [x]
push fmtOut
call printf
add esp, 16
```

Перед `call` были сняты `8 + 4 + 4 = 16` байт.

## Пример: `scanf("%d%d", &a, &b)`

```asm
sub esp, 4
push b
push a
push fmtIn
call scanf
add esp, 16
```

Здесь `4 + 12 = 16`. В `scanf` передаются адреса.

## Пример: `printf("%f", value)` через x87

```asm
sub esp, 12
fstp qword [esp + 4]
push fmtFloat
call printf
add esp, 16
```

`[esp+4..esp+11]` содержит 8-byte `double`, а `push fmtFloat` кладёт первый аргумент перед ним.

## Общая функция и wrapper

Если текущий `esp % 16` неизвестен, не угадывай padding. Либо:

1. создай выровненный frame через `and esp, -16` и восстанови исходный `esp` через frame pointer;
2. вынеси libc-call в wrapper с явно доказанным entry/exit state.

## Частые ошибки

| Ошибка | Почему неверно |
|---|---|
| считать alignment «требованием конкретной задачи» | это часть interop с современной toolchain/libc |
| очистить только argument bytes | padding останется и изменит frame state |
| добавить padding после аргументов | изменится layout параметров callee |
| считать успешный локальный запуск доказательством | libc может случайно терпеть misalignment |
| передать `[x]` в `scanf` | callee получает значение вместо адреса |

## Проверка

На breakpoint перед каждым внешним `call`:

```gdb
p/x $esp
p $esp % 16
```

Ожидается `0`. После cleanup значение `esp` должно совпасть с состоянием до подготовки вызова.
''')

    for rel, marker, block in [
        ('docs/day_06.md', '## Зачем этот день', '''## ABI-инвариант: выравнивание перед `call`

В современной GNU/Linux i386-среде одного порядка `push` и cleanup недостаточно. В полном `main` сначала создаём выровненное тело:

```asm
main:
    push ebp
    mov ebp, esp
    and esp, -16
```

После этого перед каждым внешним `call` padding и аргументы вместе должны занимать кратное 16 число байт. Для двух 32-bit аргументов: `sub esp,8`, два `push`, `call`, `add esp,16`. Для трёх: `sub esp,4`, три `push`, cleanup 16. Эпилог: `mov esp,ebp; pop ebp; ret`.

Короткий шаблон без этого frame считается только схемой порядка аргументов, а не полной ABI-корректной программой.'''),
        ('docs/day_17.md', '## Зачем этот день', '''## Дополнение к CDECL: alignment — часть контракта

CDECL определяет не только порядок параметров и владельца cleanup. Для современной i386 toolchain caller также сохраняет 16-byte call-site alignment. В выровненном body padding вычисляется по `argument_bytes`, а эпилог обязан восстановить исходный frame state. См. [точный паттерн](/patterns/libc_alignment).'''),
    ]:
        p = ROOT / rel
        text = p.read_text(encoding='utf-8')
        text = insert_before(text, marker, block, label=rel)
        write(p, text)

    p = DOCS / 'day_16.md'
    text = p.read_text(encoding='utf-8')
    text = text.replace(
        '`esp` остаётся ниже, чем должен. Следующие вызовы/возвраты могут работать неправильно.',
        '`esp` остаётся ниже контрактного значения. Во frameless-коде drift накапливается; frame-pointer эпилог может временно скрыть ошибку, но caller state всё равно восстановлен неверно до явного reset.',
    )
    text = text.replace(
        'Если не вернуть `esp` обратно, `ret` возьмёт адрес возврата не оттуда.',
        'Если перед `ret` не вернуть `esp` к адресу return address, `ret` снимет не то значение. Если эпилог сначала делает `mov esp, ebp`, локальный drift может быть сброшен, поэтому механизм нужно проверять по конкретному frame.',
    )
    write(p, text)


def patch_transfer_and_checkpoints() -> None:
    p = DOCS / 'transfer_workbook.md'
    text = p.read_text(encoding='utf-8')
    old = 'Напиши полный фрагмент `scanf("%d%d", &a, &b)` и затем `printf("%d", a-b)`. После каждого вызова укажи очистку `esp` и регистры, на сохранность которых caller не может рассчитывать.'
    new = 'Напиши полный фрагмент `scanf("%d%d", &a, &b)` и затем `printf("%d", a-b)` внутри body, где `esp % 16 == 0`. Для каждого вызова посчитай padding, argument bytes и полный cleanup; укажи регистры, на сохранность которых caller не может рассчитывать.'
    if old not in text:
        raise RuntimeError('TR-06 wording not found')
    text = text.replace(old, new, 1)
    write(p, text)

    p = DOCS / 'transfer_keys.md'
    text = p.read_text(encoding='utf-8')
    old = '- **Обязательный результат:** аргументы справа налево; для `scanf` передаются `b`, `a`, `fmt`, затем `add esp,12`; результат `a-b` передаётся `printf`, затем `add esp,8`.'
    new = '- **Обязательный результат:** body начинает вызов с `esp % 16 == 0`; `scanf`: `sub esp,4`, затем `b`, `a`, `fmt`, `call`, `add esp,16`; `printf`: `sub esp,8`, затем значение и `fmt`, `call`, `add esp,16`.'
    if old not in text:
        raise RuntimeError('TR-06 key result not found')
    text = text.replace(old, new, 1)
    text = text.replace(
        '- **Инвариант:** `scanf` получает addresses; caller очищает аргументы; `eax/ecx/edx` caller-saved.',
        '- **Инвариант:** `scanf` получает addresses; перед внешним `call` `esp % 16 == 0`; caller удаляет padding и аргументы; `eax/ecx/edx` caller-saved.',
        1,
    )
    write(p, text)

    p = DOCS / 'checkpoints.md'
    text = p.read_text(encoding='utf-8')
    old = '''Восстанови `scanf("%d", &x)`:

```asm
push ___
push ___
call scanf
add esp, ___
```

Объясни, почему передаётся адрес, а не `[x]`.'''
    new = '''Восстанови `scanf("%d", &x)` в body, где `esp % 16 == 0`:

```asm
sub esp, ___
push ___
push ___
call scanf
add esp, ___
```

Объясни, почему передаётся адрес, а не `[x]`, и докажи `esp % 16 == 0` непосредственно перед `call`.'''
    if old not in text:
        raise RuntimeError('CP2-SCANF block not found')
    text = text.replace(old, new, 1)
    write(p, text)

    p = DOCS / 'checkpoint_keys.md'
    text = p.read_text(encoding='utf-8')
    old = '- **Ожидается:** `push x; push fmt; call scanf; add esp,8` при соответствующих метках.'
    new = '- **Ожидается:** `sub esp,8; push x; push fmt; call scanf; add esp,16` при исходном `esp % 16 == 0`.'
    if old not in text:
        raise RuntimeError('CP2-SCANF key expected not found')
    text = text.replace(old, new, 1)
    text = text.replace(
        '- **Инвариант:** `scanf` получает pointer на место записи; аргументы CDECL идут справа налево; caller чистит стек.',
        '- **Инвариант:** `scanf` получает pointer на место записи; аргументы идут справа налево; перед `call` `esp % 16 == 0`; caller удаляет padding и arguments.',
        1,
    )
    rubric_marker = '## Checkpoint 1\n'
    rubric = '''### Операциональная граница `2 / 1 / 0`

- **2:** присутствуют все элементы строки `Ожидается`, итоговые состояния/числа верны и объяснён центральный `Инвариант`.
- **1:** центральный invariant и все decision-critical states верны, но есть ровно одна локальная синтаксическая, терминологическая или некритическая omission.
- **0:** неверно хотя бы одно итоговое machine state, направление operand, address/value, signedness, stack balance/alignment либо отсутствует центральный invariant.
- **Составные задания:** два и более независимых пропуска не сворачиваются в одну «локальную ошибку»; это `0` либо отдельные sub-scores, если они явно перечислены.
- **Граница 1/0:** красивое объяснение не компенсирует неверный trace, а верное число без обязательного механизма не получает `2`.
'''
    text = insert_before(text, rubric_marker, rubric, label='checkpoint operational rubric')
    write(p, text)


def patch_nan_dependency() -> None:
    p = DOCS / 'day_22.md'
    text = p.read_text(encoding='utf-8')
    block = '''## 9. Сравнения с NaN: unordered

NaN не ведёт себя как обычная числовая константа. В IEEE-модели сравнение с NaN является **unordered**:

```text
NaN == NaN  -> false
NaN <  x    -> false
NaN >  x    -> false
NaN != NaN  -> true
```

Поэтому такая проверка неверна:

```cpp
if (x == NAN) { ... }
```

Используют `std::isnan(x)` или низкоуровневую проверку unordered-состояния, когда изучены соответствующие floating-point flags.

Минимальный counterexample:

```cpp
double x = std::numeric_limits<double>::quiet_NaN();
assert(x != x);
```

Это специальное правило NaN, а не обычная потеря точности.'''
    text = insert_before(text, '## 9. Округление', block, label='Day22 NaN comparison')
    if '#### 6. Почему `x == NaN`' not in text:
        practice_marker = '---\n\n## 13. Типовые ошибки'
        practice = '''#### 6. Почему `x == NaN` не проверяет NaN?

<details>
<summary>Ответ</summary>

Потому что NaN unordered и не равен даже самому себе. Нужна `isnan` или проверка unordered-состояния.

</details>

'''
        text = text.replace(practice_marker, practice + practice_marker, 1)
    checklist_line = '- [ ] объяснить `Inf` и `NaN`;'
    if checklist_line in text and 'объяснить, почему `NaN == NaN` ложно' not in text:
        text = text.replace(checklist_line, checklist_line + '\n- [ ] объяснить, почему `NaN == NaN` ложно и как проверять NaN;', 1)
    write(p, text)


def patch_generator_and_manifest() -> None:
    manifest = '''from __future__ import annotations

DAY_RELATIVE_PATHS = tuple(f"docs/day_{i:02d}.md" for i in range(1, 26))
STANDALONE_RELATIVE_PATHS = (
    "docs/self_study.md",
    *DAY_RELATIVE_PATHS[:10],
    "docs/day_10_learning_path.md",
    *DAY_RELATIVE_PATHS[10:],
    "docs/transfer_workbook.md",
    "docs/transfer_keys.md",
    "docs/checkpoints.md",
    "docs/checkpoint_keys.md",
    "docs/ai_tutor_prompts.md",
    "docs/ai_tutor_eval.md",
)
GENERATED_RELATIVE_PATHS = (
    "docs/textbook.md",
    "docs/course_migration.md",
    "docs/closed_book_workbook.md",
)
'''
    write(ROOT / 'scripts' / 'course_manifest.py', manifest)

    generator = '''#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

from course_manifest import DAY_RELATIVE_PATHS, STANDALONE_RELATIVE_PATHS

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DAYS = [ROOT / rel for rel in DAY_RELATIVE_PATHS]
STANDALONE_SECTIONS = [ROOT / rel for rel in STANDALONE_RELATIVE_PATHS]

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
    parts.extend([
        "---", "", f"<!-- source: {path.relative_to(ROOT)} -->", "",
        path.read_text(encoding="utf-8").strip(), "",
    ])
(DOCS / "textbook.md").write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def section(text: str, title: str) -> str:
    match = re.search(rf"(?m)^## {re.escape(title)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end():]
    end = re.search(r"(?m)^## ", tail)
    return tail[:end.start() if end else None].strip()


def strip_answers(text: str) -> str:
    return re.sub(
        r"(?is)<details>\s*<summary>Ответ</summary>.*?</details>",
        "> Ответ скрыт. Сначала зафиксируй законченную попытку, затем сверяйся с канонической главой.",
        text,
    )

closed = [
    "# Closed-book workbook NASM IA-32",
    "",
    "> Сгенерированный режим без встроенных ответов. Канонические explanations остаются в `day_XX.md`.",
    "",
]
for path in DAYS:
    practice = strip_answers(section(path.read_text(encoding="utf-8"), "Практика"))
    closed.extend([
        "---", "", f"<!-- source-practice: {path.relative_to(ROOT)} -->", "",
        f"## {path.stem.replace('_', ' ').title()}", "", practice, "",
    ])
closed.extend([
    "---", "", "<!-- source-transfer: docs/transfer_workbook.md -->", "",
    (DOCS / "transfer_workbook.md").read_text(encoding="utf-8").strip(), "",
])
(DOCS / "closed_book_workbook.md").write_text("\n".join(closed).rstrip() + "\n", encoding="utf-8")

required = {"## Входные знания", "## За 30 секунд", "## Минимум после главы", "## Практика", "## Чеклист", "## Следующий шаг"}
rows = []
for path in DAYS:
    text = path.read_text(encoding="utf-8")
    present = sorted(heading for heading in required if heading in text)
    status = "structural-6/6" if len(present) == len(required) else ("transitional" if present else "legacy")
    rows.append(f"| [{path.stem.replace('_', ' ').title()}](/{path.stem}) | {status} | {len(present)}/6 |")

migration = [
    "# Структурный статус глав",
    "",
    "> Страница сгенерирована автоматически. `6/6` доказывает только наличие обязательных блоков, а не предметную корректность или retention.",
    "",
    "| Глава | Статус | Обязательные блоки |", "|---|---|---:|", *rows, "",
    "`structural-6/6` — smoke metric. Предметную корректность проверяют semantic fixtures, executable examples и review.",
]
(DOCS / "course_migration.md").write_text("\n".join(migration).rstrip() + "\n", encoding="utf-8")
'''
    write(ROOT / 'scripts' / 'generate_course_docs.py', generator)

    p = ROOT / '.gitignore'
    text = p.read_text(encoding='utf-8')
    if 'docs/closed_book_workbook.md' not in text:
        text = text.rstrip() + '\ndocs/closed_book_workbook.md\n'
    write(p, text)

    p = ROOT / 'package.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    clean = data['scripts']['docs:clean']
    if 'docs/closed_book_workbook.md' not in clean:
        data['scripts']['docs:clean'] = clean + ' docs/closed_book_workbook.md'
    write(p, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    p = ROOT / 'README.md'
    text = p.read_text(encoding='utf-8')
    if 'docs/closed_book_workbook.md' not in text:
        text = text.replace(
            '| Generated route `/textbook` | полный самостоятельный учебник; создаётся перед VitePress build |',
            '| Generated route `/textbook` | полный самостоятельный учебник; создаётся перед VitePress build |\n| [Closed-book workbook](docs/closed_book_workbook.md) | практика без встроенных ответов; generated перед build |',
            1,
        )
    write(p, text)

    p = DOCS / 'self_study.md'
    text = p.read_text(encoding='utf-8')
    if '](/closed_book_workbook)' not in text:
        text = text.replace(
            'Не открывай ответы до законченной попытки.',
            'Не открывай ответы до законченной попытки. Для режима без технической возможности случайно раскрыть `<details>` используй [closed-book workbook](/closed_book_workbook).',
            1,
        )
    write(p, text)

    p = DOCS / '.vitepress' / 'config.mts'
    text = p.read_text(encoding='utf-8')
    if 'link: "/closed_book_workbook"' not in text:
        needle = '{ text: "Полный самостоятельный учебник", link: "/textbook" }'
        repl = needle + ',\n                    { text: "Closed-book workbook", link: "/closed_book_workbook" }'
        if needle not in text:
            raise RuntimeError('VitePress textbook nav item not found')
        text = text.replace(needle, repl, 1)
    write(p, text)


def normalize_contract(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def add_transfer_fingerprints() -> None:
    workbook_path = DOCS / 'transfer_workbook.md'
    keys_path = DOCS / 'transfer_keys.md'
    workbook = workbook_path.read_text(encoding='utf-8')
    keys = keys_path.read_text(encoding='utf-8')

    def sections(text: str) -> dict[str, str]:
        matches = list(re.finditer(r'(?m)^## (TR-\d{2})\b.*$', text))
        result: dict[str, str] = {}
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            result[match.group(1)] = text[match.end():end].strip()
        return result

    task_sections = sections(workbook)
    for transfer_id, body in task_sections.items():
        digest = hashlib.sha256(normalize_contract(body).encode('utf-8')).hexdigest()
        heading = re.compile(rf'(?m)^(## {re.escape(transfer_id)}\b[^\n]*\n)(?:<!-- task-sha256: [0-9a-f]{{64}} -->\n)?')
        keys, count = heading.subn(rf'\1<!-- task-sha256: {digest} -->\n', keys, count=1)
        if count != 1:
            raise RuntimeError(f'key heading not found for {transfer_id}')
    write(keys_path, keys)


def patch_ai_eval() -> None:
    path = ROOT / 'evals' / 'ai_tutor_cases.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    mapping = {
        'AI-01-one-question': ('1. Универсальный наставник по главе', ['docs/day_03.md']),
        'AI-02-no-early-solution': ('5. Разбор моего решения', ['docs/day_09.md']),
        'AI-03-ia32-boundary': ('2. Совместное изучение новой темы', ['docs/day_17.md', 'docs/c_abi.md']),
        'AI-04-unseen-material': ('3. Режим строгого зачёта', ['docs/day_04.md']),
        'AI-05-recovery-switch': ('4. Диагностика непонимания', ['docs/day_05.md']),
        'AI-06-third-failure-prerequisite': ('4. Диагностика непонимания', ['docs/day_16.md', 'docs/day_17.md']),
        'AI-07-reverse-uncertainty': ('5. Разбор моего решения', ['docs/day_24.md']),
        'AI-08-x87-order': ('3. Режим строгого зачёта', ['docs/day_23.md']),
        'AI-09-same-session-vs-spaced': ('2. Совместное изучение новой темы', ['docs/day_09.md']),
        'AI-10-insufficient-data': ('7. Компактный prompt для DeepSeek или маленького context window', []),
    }
    for item in data['cases']:
        heading, chapters = mapping[item['id']]
        item['prompt_heading'] = heading
        item['chapter_files'] = chapters
        item['input_contract'] = {'task': item['task'], 'answer': item['learner_answer']}
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    p = DOCS / 'ai_tutor_eval.md'
    text = p.read_text(encoding='utf-8')
    block = '''## Воспроизводимая сборка case

Каждый case обязан хранить:

- точный `prompt_heading`, выбирающий один fenced prompt mode;
- `chapter_files` в фиксированном порядке;
- `input_contract.task` и `input_contract.answer`;
- `must`/`must_not` как scoring contract.

Harness собирает полный input только из этих полей и сохраняет его вместе с output. Пустой `chapter_files` допустим только для кейса, который проверяет реакцию на отсутствующее условие. Это делает provider-run повторяемым, но не превращает static fixture в доказательство поведения модели.'''
    text = insert_before(text, '## Минимальный provider-run', block, label='AI eval reproducibility')
    write(p, text)


def patch_validator() -> None:
    p = ROOT / 'scripts' / 'validate_course.py'
    text = p.read_text(encoding='utf-8')
    if 'from course_manifest import' not in text:
        text = text.replace(
            'import re\n',
            'import re\nimport hashlib\n\nfrom course_manifest import DAY_RELATIVE_PATHS, GENERATED_RELATIVE_PATHS, STANDALONE_RELATIVE_PATHS\n',
            1,
        )
    block_marker = '# Review-remediation semantic and generator invariants.'
    if block_marker not in text:
        block = r'''
# Review-remediation semantic and generator invariants.

def normalized_contract(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


if textbook.is_file():
    actual_sources = re.findall(r"<!-- source: ([^ ]+) -->", textbook.read_text(encoding="utf-8"))
    if actual_sources != list(STANDALONE_RELATIVE_PATHS):
        errors.append(f"generated textbook source manifest mismatch: {actual_sources}")
closed_book = DOCS / "closed_book_workbook.md"
if not closed_book.is_file():
    errors.append("missing generated docs/closed_book_workbook.md")
else:
    closed_text = closed_book.read_text(encoding="utf-8")
    practice_sources = re.findall(r"<!-- source-practice: ([^ ]+) -->", closed_text)
    if practice_sources != list(DAY_RELATIVE_PATHS):
        errors.append(f"closed-book practice manifest mismatch: {practice_sources}")
    if "<summary>Ответ</summary>" in closed_text:
        errors.append("closed-book workbook leaks inline answers")


ai_prompt_text = (DOCS / "ai_tutor_prompts.md").read_text(encoding="utf-8")
prompt_blocks = [
    block for block in re.findall(r"```text\n(.*?)```", ai_prompt_text, flags=re.S)
    if any(tag in block for tag in ("<task>", "<chapter>", "<answer>"))
]
if len(prompt_blocks) < 7:
    errors.append(f"expected at least seven structured AI prompt blocks, found {len(prompt_blocks)}")
for index, block in enumerate(prompt_blocks, start=1):
    for tag in ("task", "chapter", "answer"):
        if block.count(f"<{tag}>") != 1 or block.count(f"</{tag}>") != 1:
            errors.append(f"AI prompt block {index} has invalid <{tag}> contract")


if cases_path.is_file():
    cases_data = json.loads(cases_path.read_text(encoding="utf-8"))
    prompt_headings = {h.title for h in headings_outside_fences(ai_prompt_text)}
    for item in cases_data.get("cases", []):
        case_id = item.get("id")
        heading = item.get("prompt_heading")
        chapters = item.get("chapter_files")
        contract = item.get("input_contract")
        if heading not in prompt_headings:
            errors.append(f"AI case {case_id} references unknown prompt heading: {heading!r}")
        if not isinstance(chapters, list):
            errors.append(f"AI case {case_id} lacks chapter_files list")
        else:
            for rel in chapters:
                if not (ROOT / rel).is_file():
                    errors.append(f"AI case {case_id} references missing chapter fixture: {rel}")
        if not isinstance(contract, dict) or set(contract) != {"task", "answer"}:
            errors.append(f"AI case {case_id} lacks exact input_contract")
        if case_id != "AI-10-insufficient-data" and not chapters:
            errors.append(f"AI case {case_id} must provide at least one chapter fixture")


def transfer_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^## (TR-\d{2})\b.*$", text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1)] = text[match.end():end].strip()
    return result

_task_sections = transfer_sections(workbook)
_key_sections = transfer_sections(keys)
for transfer_id in expected_transfer_ids:
    digest = hashlib.sha256(normalized_contract(_task_sections[transfer_id]).encode("utf-8")).hexdigest()
    if f"<!-- task-sha256: {digest} -->" not in _key_sections[transfer_id]:
        errors.append(f"{transfer_id} key fingerprint does not match current task")


def x87_program(section: str) -> list[str]:
    fenced = re.search(r"```asm\n(.*?)```", section, flags=re.S)
    source = fenced.group(1) if fenced else ""
    if not source:
        inline = next((value for value in re.findall(r"`([^`]+)`", section) if "fld" in value), "")
        source = inline.replace(";", "\n")
    return [re.sub(r"\s+", " ", line.strip().lower()) for line in source.splitlines() if line.strip()]


def simulate_x87(lines: list[str], values: dict[str, float]) -> list[float]:
    stack: list[float] = []
    for line in lines:
        load = re.match(r"fld(?: dword| qword)? \[?([a-z][a-z0-9_]*)\]?", line)
        if load:
            stack.insert(0, values[load.group(1)])
            continue
        if line.startswith("faddp"):
            stack = [stack[1] + stack[0], *stack[2:]]
        elif line.startswith("fsubp"):
            stack = [stack[1] - stack[0], *stack[2:]]
        elif line.startswith("fmulp"):
            stack = [stack[1] * stack[0], *stack[2:]]
        elif line.startswith("fdivp"):
            stack = [stack[1] / stack[0], *stack[2:]]
    return stack

for label, section, values, expected in (
    ("TR-23", _key_sections["TR-23"], {"a": 10.0, "b": 4.0, "c": 1.0, "d": 2.0}, 2.0),
    (
        "CP5-X87-TRANSFER",
        section_text(checkpoint_keys, headings_outside_fences(checkpoint_keys), "CP5-X87-TRANSFER"),
        {"a": 10.0, "b": 4.0, "c": 3.0},
        2.0,
    ),
):
    try:
        stack = simulate_x87(x87_program(section), values)
    except (IndexError, KeyError, ZeroDivisionError) as exc:
        errors.append(f"{label} x87 semantic fixture failed to execute: {exc}")
    else:
        if len(stack) != 1 or abs(stack[0] - expected) > 1e-9:
            errors.append(f"{label} x87 operand order/depth is wrong: stack={stack}, expected={expected}")


def validate_example_stack_alignment(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    delta: int | None = None
    saw_external = False
    for number, raw in enumerate(lines, start=1):
        line = raw.split(";", 1)[0].strip().lower()
        if not line:
            continue
        if line == "and esp, -16":
            delta = 0
            continue
        if delta is None:
            continue
        if line.startswith("push "):
            delta -= 4
        elif line.startswith("pop "):
            delta += 4
        else:
            match = re.match(r"(add|sub) esp,\s*(\d+)$", line)
            if match:
                amount = int(match.group(2))
                delta += amount if match.group(1) == "add" else -amount
            elif line.startswith("mov esp, ebp"):
                delta = None
        if line in {"call printf", "call scanf"}:
            saw_external = True
            if delta % 16 != 0:
                errors.append(f"misaligned external call in {path.relative_to(ROOT)}:{number}: esp delta {delta}")
    if saw_external:
        text_value = path.read_text(encoding="utf-8")
        for marker in ("push ebp", "mov ebp, esp", "and esp, -16", "mov esp, ebp", "pop ebp"):
            if marker not in text_value:
                errors.append(f"{path.relative_to(ROOT)} lacks aligned-frame marker {marker!r}")

for example in (ROOT / "examples").glob("*.asm"):
    validate_example_stack_alignment(example)


day22_text = (DOCS / "day_22.md").read_text(encoding="utf-8")
for marker in ("unordered", "NaN == NaN", "isnan"):
    if marker not in day22_text:
        errors.append(f"Day 22 lacks prerequisite for CP5-NAN: {marker!r}")

for marker in ("Операциональная граница", "Составные задания", "Граница 1/0"):
    if marker not in checkpoint_keys:
        errors.append(f"checkpoint scoring rubric lacks marker {marker!r}")
'''
        text = text.replace('\nif errors:\n', '\n' + block.strip() + '\n\nif errors:\n', 1)
    text = text.replace(
        'for generated in (DOCS / "textbook.md", DOCS / "course_migration.md"):',
        'for generated in (DOCS / "textbook.md", DOCS / "course_migration.md", DOCS / "closed_book_workbook.md"):')
    text = text.replace(
        'if path.name in {"textbook.md", "course_migration.md"}:',
        'if path.name in {"textbook.md", "course_migration.md", "closed_book_workbook.md"}:')
    if '"/closed_book_workbook",' not in text:
        text = text.replace('    "/day_10_learning_path",\n', '    "/day_10_learning_path",\n    "/closed_book_workbook",\n', 1)
    write(p, text)


def main() -> None:
    patch_markdown_calls()
    patch_examples()
    patch_alignment_docs()
    patch_transfer_and_checkpoints()
    patch_nan_dependency()
    patch_generator_and_manifest()
    add_transfer_fingerprints()
    patch_ai_eval()
    patch_validator()

    required_changed = {
        'docs/c_abi.md',
        'docs/day_06.md',
        'docs/day_17.md',
        'docs/day_22.md',
        'docs/transfer_workbook.md',
        'docs/transfer_keys.md',
        'docs/checkpoints.md',
        'docs/checkpoint_keys.md',
        'scripts/validate_course.py',
        'scripts/generate_course_docs.py',
        'scripts/course_manifest.py',
        'docs/patterns/libc_alignment.md',
    }
    missing = sorted(required_changed.difference(changed))
    if missing:
        raise RuntimeError(f'expected remediation files did not change: {missing}')
    print('Remediation changed files:')
    for rel in sorted(changed):
        print(rel)


if __name__ == '__main__':
    main()
