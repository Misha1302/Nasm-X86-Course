# День 23. x87: вещественные числа как стек

## Опора на материалы ВШЭ

`Slides2026-0x10.pdf`: x87, `FINIT`, `st0..st7`, `fld/fstp/faddp`, печать через `printf`.

## Зачем этот день

x87 не похож на `eax/ebx`. Это стековая машина: числа кладутся на верхушку, операции берут верхние элементы.

## Главная мысль

`fld` — push, `faddp` — add+pop, `fstp` — store+pop. Для `printf("%f")` нужен `double`, то есть `qword`.

## x87 stack

```text
x87 register stack:

+-----------+
|   st(7)   |
+-----------+
|   ...     |
+-----------+
|   st(1)   |  y
+-----------+
|   st(0)   |  x  <- top
+-----------+
```

## Пример сложения

```asm
finit
fld dword [x]
fld dword [y]
faddp
fstp dword [z]
```

После `fld x`: на вершине `x`. После `fld y`: на вершине `y`, под ним `x`. `faddp` складывает и снимает один элемент.

## Печать через `printf`

`printf("%f")` в C ждёт `double`, даже если исходно у тебя `float`. Поэтому для передачи в `printf` нужно 8 байт:

```asm
sub esp, 12
fstp qword [esp+4]
mov dword [esp], fmt
call printf
add esp, 12
```

Типовая ошибка:

```asm
fstp dword [esp+4] ; плохо для printf("%f")
```

## Команды

| Instruction | Meaning |
|---|---|
| `finit` | initialize x87 |
| `fld` | push floating value |
| `fst` | store without pop |
| `fstp` | store and pop |
| `faddp` | add and pop |
| `fsubp` | subtract and pop |
| `fmulp` | multiply and pop |
| `fdivp` | divide and pop |

## Мини-челленджи

1. Нарисуй x87 stack после `fld x; fld y`.
2. Что делает `faddp`?
3. Почему `%f` ждёт `qword`?
4. Чем x87 напоминает обратную польскую запись?

<details>
<summary>Ответы / подсказки</summary>

1. `st0=y`, `st1=x`.
2. Складывает верхние элементы и делает pop.
3. В variadic `printf` значение для `%f` передаётся как `double`.
4. Операнды сначала кладутся на стек, потом операция берёт их со стека.

</details>

---
