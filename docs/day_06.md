# День 06. Первая настоящая программа: читаем число и печатаем ответ

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-07.pdf`: базовая NASM-программа, стековые аргументы, вызовы функций.

## Зачем этот день

Сегодня NASM превращается в инструмент для задач. Мы читаем число, считаем ответ и печатаем. Теорию CDECL разберём позже, но рабочий шаблон нужен уже сейчас.

## Главная мысль

`scanf` получает адрес, `printf` получает значение. Аргументы кладём через `push`, после вызова чистим стек.

## Базовый шаблон

```asm
section .data
    fmtIn db "%d", 0
    fmtOut db "%d", 10, 0

section .bss
    x resd 1

section .text
    extern scanf
    extern printf
    global main

main:
    push x              ; &x
    push fmtIn
    call scanf
    add esp, 8

    push dword [x]      ; x
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

## Почему порядок `push` такой странный

В 32-битном CDECL аргументы кладутся справа налево.

C:

```c
scanf("%d", &x);
```

NASM:

```asm
push x       ; второй аргумент
push fmtIn   ; первый аргумент
call scanf
add esp, 8
```

## Почему после вызова `add esp, 8`

Мы положили два аргумента по 4 байта. После вызова их надо убрать со стека.

```text
2 arguments * 4 bytes = 8 bytes
```

## Таблица

| C | NASM |
|---|---|
| `scanf("%d", &x)` | `push x`, `push fmtIn`, `call scanf` |
| `printf("%d", x)` | `push dword [x]`, `push fmtOut`, `call printf` |
| 2 аргумента | `add esp, 8` |
| 3 аргумента | `add esp, 12` |

## Мини-челленджи

1. Программа: ввод `x`, вывод `x`.
2. Программа: ввод `a b`, вывод `a+b`.
3. Программа: ввод `a b c`, вывод `a*b+c`.

<details>
<summary>Подсказка для `a+b`</summary>

После чтения:

```asm
mov eax, [a]
add eax, [b]
```

Потом печатаем `eax` через `printf`: сначала `push eax`, потом `push fmtOut`.

</details>

## Типовые ошибки

- `push [x]` для `scanf` вместо `push x`;
- `push [fmtIn]` вместо `push fmtIn`;
- забыть `add esp, 8`;
- не указать `dword`, когда NASM не может сам понять размер.

---
