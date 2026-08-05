#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"missing reviewed supplementary page: {relative}")
    return path.read_text(encoding="utf-8")


def require(text: str, markers: tuple[str, ...], owner: str) -> None:
    for marker in markers:
        if marker not in text:
            raise AssertionError(f"{owner} lacks reviewed contract marker {marker!r}")


def forbid(text: str, markers: tuple[str, ...], owner: str) -> None:
    for marker in markers:
        if marker in text:
            raise AssertionError(f"{owner} contains rejected wording or unsafe shortcut {marker!r}")


def main() -> int:
    branchless = read("docs/patterns/branchless.md")
    require(
        branchless,
        (
            "Граница `INT32_MIN`",
            "neg edx",
            "adc eax, 0",
            "формула `(a+b-1)/b` без проверки диапазона",
            "смешение знаковой и беззнаковой интерпретации",
        ),
        "branchless",
    )
    forbid(
        branchless,
        (
            "забыть беззнаковая/знаковая интерпретация смысл",
            "ceil(a / b) = (a + b - 1) / b\n```\n\nПример",
        ),
        "branchless",
    )

    bits = read("docs/patterns/bit_counting.md")
    require(
        bits,
        (
            "uint32_t mask = K == 32 ? UINT32_MAX",
            "аппаратно учитываются только младшие 5 бит счётчика",
            "Для `K = 32` маску надо задать отдельно",
            "Для беззнаковых значений используй `shr`",
            "случай `x = 0`",
        ),
        "bit_counting",
    )
    forbid(bits, ("Для беззнаковые числа-чисел", "Не делай `1 << 32`: для 32-bit это опасная граница."), "bit_counting")

    decimal = read("docs/patterns/decimal.md")
    require(
        decimal,
        (
            "rev * 10 + digit",
            "64-битные промежуточные значения",
            "знаменатель был положительным",
            "Для `x = 0`",
        ),
        "decimal",
    )

    strings = read("docs/patterns/strings_files.md")
    require(
        strings,
        (
            'fmtWord db "%1000s", 0',
            "Проверь, что `scanf` вернул `1`",
            "после `fopen` сначала проверь `eax`",
            "%s` без ограничения ширины",
        ),
        "strings_files",
    )
    forbid(strings, ('`scanf("%s", s)` | прочитать слово',), "strings_files")

    recursion = read("docs/patterns/recursion.md")
    require(
        recursion,
        (
            "примерный размер кадра × максимальная глубина",
            "EFLAGS",
            "Все ветви должны приходить к согласованному эпилогу",
        ),
        "recursion",
    )

    linked = read("docs/patterns/array_linked_list.md")
    require(
        linked,
        (
            "значения уникальны",
            "из head достижимы ровно N различных элементов",
            "текущего сегмента",
            "ограничь число шагов вывода значением `N`",
        ),
        "array_linked_list",
    )

    stack = read("docs/patterns/advanced_stack.md")
    require(
        stack,
        (
            "args_bytes = 4 * (n + 1)",
            "padding + args_bytes",
            "ограничивать `n`",
            "Сам адрес `fn`",
        ),
        "advanced_stack",
    )

    bigint = read("docs/patterns/bigint.md")
    require(
        bigint,
        (
            "abs(INT32_MIN)",
            "high : mid : low",
            "потерять `p_hi` при втором `mul`",
            "печатать `-0`",
        ),
        "bigint",
    )
    forbid(
        bigint,
        (
            "несколькими 32-битных словами",
            "64-битный делимое",
            "вывести десятичном виде",
        ),
        "bigint",
    )

    print("SUPPLEMENTARY_REVIEWED_PAGES=8")
    print("SUPPLEMENTARY_REVIEW_REGRESSIONS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
