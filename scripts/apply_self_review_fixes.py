#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
changed: list[str] = []


def write(path: Path, text: str) -> None:
    old = path.read_text(encoding="utf-8")
    if old != text:
        path.write_text(text, encoding="utf-8")
        changed.append(str(path.relative_to(ROOT)))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def patch_complete_asm_block(block: str) -> str:
    if "global main" not in block or "main:" not in block:
        return block
    if not re.search(r"(?m)^\s*call\s+", block):
        return block

    main_match = re.search(r"(?m)^(?P<i>[ \t]*)main:\s*$", block)
    if main_match is None:
        return block
    main_tail = block[main_match.end():]

    if "and esp, -16" not in main_tail:
        indent = main_match.group("i") + "    "
        prologue = (
            f"\n{indent}push ebp\n"
            f"{indent}mov ebp, esp\n"
            f"{indent}and esp, -16"
        )
        block = block[:main_match.end()] + prologue + block[main_match.end():]

    main_match = re.search(r"(?m)^[ \t]*main:\s*$", block)
    assert main_match is not None
    main_tail = block[main_match.end():]
    if "mov esp, ebp" not in main_tail:
        return_pattern = re.compile(
            r"(?m)^(?P<i>[ \t]*)xor eax, eax\s*\n(?P=i)ret\s*$"
        )
        matches = list(return_pattern.finditer(main_tail))
        if not matches:
            raise RuntimeError("complete main with calls lacks canonical xor/ret epilogue")
        match = matches[-1]
        indent = match.group("i")
        replacement = (
            f"{indent}mov esp, ebp\n"
            f"{indent}pop ebp\n"
            f"{indent}xor eax, eax\n"
            f"{indent}ret"
        )
        start = main_match.end() + match.start()
        end = main_match.end() + match.end()
        block = block[:start] + replacement + block[end:]
    return block


def patch_complete_markdown_programs() -> None:
    fence = re.compile(r"```asm\n(.*?)```", flags=re.S)
    for path in DOCS.rglob("*.md"):
        if path.name in {"textbook.md", "course_migration.md", "closed_book_workbook.md"}:
            continue
        text = path.read_text(encoding="utf-8")
        new = fence.sub(lambda m: "```asm\n" + patch_complete_asm_block(m.group(1)) + "```", text)
        write(path, new)


def patch_saved_value_alignment() -> None:
    # One saved dword is already on the stack. For two 32-bit call arguments,
    # only 4 padding bytes are needed; the call-local cleanup is 12 bytes.
    pattern = re.compile(
        r"(?P<i>^[ \t]*)push (?P<reg>eax|ecx|edx)\s*(?P<c>;[^\n]*)?\n"
        r"(?P<gap>(?:[ \t]*\n)*)"
        r"(?P=i)sub esp, 8(?P<pad>[^\n]*)\n"
        r"(?P<body>(?:(?P=i).+\n){3})"
        r"(?P=i)add esp, 16\n"
        r"(?P=i)pop (?P=reg)",
        flags=re.M,
    )
    for rel in ("docs/c_abi.md", "docs/day_17.md", "docs/debug_cards.md"):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        text, count = pattern.subn(
            lambda m: (
                f"{m.group('i')}push {m.group('reg')}{m.group('c') or ''}\n"
                f"{m.group('gap')}"
                f"{m.group('i')}sub esp, 4       ; saved dword + 4 padding + 8 argument bytes = 16\n"
                f"{m.group('body')}"
                f"{m.group('i')}add esp, 12\n"
                f"{m.group('i')}pop {m.group('reg')}"
            ),
            text,
        )
        if rel == "docs/c_abi.md" and count < 1:
            raise RuntimeError("saved-value alignment example was not found in c_abi.md")
        write(path, text)


def patch_day06_contract() -> None:
    path = DOCS / "day_06.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "- После вызова caller чистит стек: `add esp, argument_count * 4`.",
        "- Caller удаляет весь call area: `padding + argument bytes`.",
    )
    text = text.replace(
        "- посчитать, сколько байт убрать из стека;",
        "- посчитать padding, argument bytes и полный cleanup;",
    )
    text = text.replace("- stack alignment.\n", "")
    text = text.replace(
        "Отсюда следует `add esp, 8` после двух аргументов. В [дне 16](/day_16) мы разберём точную механику `push/call/ret`, а в [дне 17](/day_17) построим полный frame layout и объясним ответственность caller/callee.",
        "Если выровненный body начинает с `esp % 16 == 0`, два 32-bit аргумента требуют `sub esp,8`, двух `push` и `add esp,16`. В [дне 16](/day_16) мы разберём `push/call/ret`, а в [дне 17](/day_17) построим полный frame и ответственность caller/callee.",
    )
    write(path, text)


def patch_c_abi_prose_and_internal_call() -> None:
    path = DOCS / "c_abi.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "Почему `12`?\n\n```text\n8 bytes double + 4 bytes format pointer = 12 bytes\n```",
        "Почему `sub esp,12`?\n\n```text\n8 bytes double + 4 bytes padding = 12 bytes reserved\nпосле push format: 4 + 8 + 4 = 16 bytes total call area\n```",
    )
    old_section = '''## 17. Stack alignment: коротко и честно

В простых учебных IA-32 задачах обычно достаточно держать стек **сбалансированным**: сколько положил через `push`, столько убрал через `add esp, ...` или `pop`.

Но в реальных ABI и с современными компиляторами может быть дополнительное требование к выравниванию стека, особенно вокруг SSE и библиотечных вызовов.

Практическое правило для курса:

1. Не порти `esp` без причины.
2. После каждого CDECL-вызова убирай аргументы.
3. Перед вызовом libc не оставляй стек в случайном состоянии.
4. Если пишешь сложную функцию с локальными данными и вызовами, следи за выравниванием отдельно.

Для наших базовых задач главная ошибка почти всегда не “идеальное 16-byte alignment”, а забытый `add esp, ...` или неправильный аргумент.'''
    new_section = '''## 17. Stack alignment: часть ABI, а не необязательная оптимизация

В поддерживаемой GNU/Linux i386-среде перед каждым ABI-вызовом доказываем два независимых условия:

1. параметры лежат непрерывно и в правильном порядке;
2. непосредственно перед `call` выполняется `esp % 16 == 0`.

Баланс после возврата также обязателен: caller удаляет **padding + argument bytes**. Успешный случайный запуск misaligned-кода не доказывает корректность. Полная формула и wrapper-стратегия находятся в [паттерне libc alignment](/patterns/libc_alignment).'''
    text = replace_once(text, old_section, new_section, "c_abi alignment section")
    text = text.replace(
        "    push 7\n    push 5\n    call sum\n    add esp, 8",
        "    sub esp, 8       ; padding: 8 + 8 argument bytes = 16\n    push 7\n    push 5\n    call sum\n    add esp, 16",
        1,
    )
    write(path, text)


def patch_x87_assessment_contracts() -> None:
    path = DOCS / "transfer_keys.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "затем `sub esp,8; fstp qword [esp]; push fmt; call printf; add esp,12`.",
        "затем при aligned body `sub esp,12; fstp qword [esp]; push fmt; call printf; add esp,16`.",
    )
    text = text.replace(
        "`%f` — 8-байтовый double плюс 4-байтовый format pointer, очистка 12 байт.",
        "`%f` — 8-байтовый double плюс 4-байтовый format pointer; при aligned body добавляются 4 байта padding и cleanup равен 16.",
    )
    write(path, text)

    path = DOCS / "checkpoints.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "### CP5-VARARGS — Пропуски: `%f`\n\n```asm",
        "### CP5-VARARGS — Пропуски: `%f`\n\nBody начинает с `esp % 16 == 0`. Восстанови непрерывный layout аргументов:\n\n```asm",
        1,
    )
    write(path, text)

    path = DOCS / "checkpoint_keys.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "- **Ожидается:** `sub esp,8; fstp qword [esp]; push fmt; call printf; add esp,12`.",
        "- **Ожидается:** `sub esp,12; fstp qword [esp]; push fmt; call printf; add esp,16` при исходном `esp % 16 == 0`.",
    )
    text = text.replace(
        "- **Инвариант:** `%f` в variadic `printf` читает `double`, то есть 8 байт, плюс 4-байтовый pointer формата.",
        "- **Инвариант:** `%f` читает непрерывный 8-byte `double`; format pointer занимает 4 байта; padding лежит выше аргументов; перед `call` `esp % 16 == 0`.",
    )
    write(path, text)


def patch_day22_numbering() -> None:
    path = DOCS / "day_22.md"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "## 9. Округление", "## 10. Округление", "Day22 rounding heading")
    text = replace_once(text, "## 10. Почему порядок операций важен", "## 11. Почему порядок операций важен", "Day22 order heading")
    text = replace_once(text, "## 11. Связь с x87", "## 12. Связь с x87", "Day22 x87 heading")
    write(path, text)


def patch_readme_generated_route() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "| [Closed-book workbook](docs/closed_book_workbook.md) | практика без встроенных ответов; generated перед build |",
        "| Generated route `/closed_book_workbook` | практика без встроенных ответов; создаётся перед VitePress build |",
    )
    write(path, text)


def strengthen_validator() -> None:
    path = ROOT / "scripts" / "validate_course.py"
    text = path.read_text(encoding="utf-8")
    marker = "day22_text = (DOCS / \"day_22.md\").read_text(encoding=\"utf-8\")"
    if "complete Markdown main lacks aligned frame" not in text:
        block = r'''

def validate_complete_markdown_mains(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    for block_index, block in enumerate(re.findall(r"```asm\n(.*?)```", source, flags=re.S), start=1):
        if "global main" not in block or "main:" not in block or not re.search(r"(?m)^\s*call\s+", block):
            continue
        main_tail = block.split("main:", 1)[1]
        for required in ("push ebp", "mov ebp, esp", "and esp, -16", "mov esp, ebp", "pop ebp"):
            if required not in main_tail:
                errors.append(
                    f"complete Markdown main lacks aligned frame {required!r}: "
                    f"{path.relative_to(ROOT)} block {block_index}"
                )

for markdown in DOCS.rglob("*.md"):
    if markdown.name not in {"textbook.md", "course_migration.md", "closed_book_workbook.md"}:
        validate_complete_markdown_mains(markdown)

for rel in ("docs/transfer_keys.md", "docs/checkpoint_keys.md"):
    assessment = (ROOT / rel).read_text(encoding="utf-8")
    if "fstp qword [esp]; push fmt; call printf; add esp,12" in assessment:
        errors.append(f"stale x87 variadic cleanup remains in {rel}")

if re.search(r"(?m)^## 9\. .+\n(?:.|\n)*?^## 9\. ", (DOCS / "day_22.md").read_text(encoding="utf-8")):
    errors.append("Day 22 contains duplicate numbered section 9")

for rel in ("docs/c_abi.md", "docs/day_17.md", "docs/debug_cards.md"):
    source = (ROOT / rel).read_text(encoding="utf-8")
    if re.search(
        r"push (eax|ecx|edx).*?sub esp, 8.*?call printf.*?add esp, 16.*?pop \\1",
        source,
        flags=re.S,
    ):
        errors.append(f"saved dword was omitted from call-site padding calculation: {rel}")

'''
        if text.count(marker) != 1:
            raise RuntimeError("validator insertion marker mismatch")
        text = text.replace(marker, block + marker, 1)
    text = text.replace(
        "from course_manifest import DAY_RELATIVE_PATHS, GENERATED_RELATIVE_PATHS, STANDALONE_RELATIVE_PATHS",
        "from course_manifest import DAY_RELATIVE_PATHS, GENERATED_RELATIVE_PATHS, STANDALONE_RELATIVE_PATHS",
    )
    write(path, text)


def main() -> None:
    patch_complete_markdown_programs()
    patch_saved_value_alignment()
    patch_day06_contract()
    patch_c_abi_prose_and_internal_call()
    patch_x87_assessment_contracts()
    patch_day22_numbering()
    patch_readme_generated_route()
    strengthen_validator()
    if not changed:
        raise RuntimeError("self-review fix pass changed no files")
    print("Self-review fixes changed:")
    for rel in sorted(set(changed)):
        print(rel)


if __name__ == "__main__":
    main()
