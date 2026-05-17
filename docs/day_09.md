# День 09. Деление: `edx:eax`, `div`, `idiv`

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-06.pdf`: `mul`, `imul`, `div`, `idiv`, пара `edx:eax`, подготовка делимого через `cdq`.

## За 30 секунд

- `div` — unsigned division.
- `idiv` — signed division.
- Делимое для 32-bit деления лежит в `edx:eax`.
- Делитель — один явный операнд.
- Частное после деления лежит в `eax`.
- Остаток после деления лежит в `edx`.
- Перед `idiv` обычно нужен `cdq`.
- Перед `div` обычно нужен `xor edx, edx`.

## Минимум после главы

Ты должен уметь:

- написать signed `a / b`;
- написать signed `a % b`;
- написать unsigned `a / b`;
- объяснить, зачем нужен `edx`;
- объяснить, почему забытый `cdq` ломает код;
- не писать несуществующее `idiv eax, ecx`.

Можно пока не заучивать:

- все формы `mul/imul`;
- overflow-детали полного 64-битного умножения;
- редкие исключения деления вне учебных задач.

---

## Главная схема

```text
Before division:

+----------------+----------------+
|      EDX       |      EAX       |
+----------------+----------------+
   high 32 bits      low 32 bits

idiv divisor

After division:

EAX = quotient
EDX = remainder
```

---

## Базовые шаблоны

### Signed division

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

### Unsigned division

```asm
mov eax, [x]
xor edx, edx
div dword [y]
; eax = x / y
; edx = x % y
```

---

## Почему не хватает одного `eax`

`idiv` не делит просто `eax`.

Для 32-bit деления процессор берёт 64-bit делимое из пары `edx:eax`.

Поэтому перед делением надо подготовить обе половины:

| Случай | Как подготовить |
|---|---|
| signed `int x` в `eax` | `cdq` |
| unsigned `uint32_t x` в `eax` | `xor edx, edx` |

---

## `cdq` перед `idiv`

`cdq` расширяет знак `eax` в `edx:eax`.

| `eax` | После `cdq`: `edx` | Смысл |
|---|---|---|
| положительный | `00000000h` | верхняя половина нулевая |
| отрицательный | `FFFFFFFFh` | знак размножен |

Пример для `x = -7`:

```text
eax = FFFFFFF9
edx = FFFFFFFF
edx:eax = FFFFFFFFFFFFFFF9 = -7 как 64-bit signed
```

---

## Умножение: что нужно знать сейчас

Для учебных задач чаще всего удобна форма:

```asm
imul eax, [b]        ; eax = eax * b
imul eax, ecx, 41    ; eax = ecx * 41
```

Есть и историческая форма:

```asm
mul ecx     ; unsigned: edx:eax = eax * ecx
imul ecx    ; signed:   edx:eax = eax * ecx
```

Но для первых задач обычно достаточно удобной формы `imul destination, source`.

---

## Полный пример: частное `a / b`

```asm
section .data
    fmtIn db "%d", 0
    fmtOut db "%d", 10, 0

section .bss
    a resd 1
    b resd 1

section .text
    extern scanf
    extern printf
    global main

main:
    push a
    push fmtIn
    call scanf
    add esp, 8

    push b
    push fmtIn
    call scanf
    add esp, 8

    mov eax, [a]
    cdq
    idiv dword [b]

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

Чтобы напечатать остаток, печатай `edx`:

```asm
push edx
push fmtOut
call printf
add esp, 8
```

---

## Трассировка `-7 / 3`

```asm
mov eax, -7
cdq
mov ecx, 3
idiv ecx
```

| Шаг | EAX | EDX | ECX | Смысл |
|---|---|---|---|---|
| after `mov eax, -7` | `FFFFFFF9` | ? | ? | `eax = -7` |
| after `cdq` | `FFFFFFF9` | `FFFFFFFF` | ? | `edx:eax = -7` |
| after `mov ecx, 3` | `FFFFFFF9` | `FFFFFFFF` | `00000003` | делитель = 3 |
| after `idiv ecx` | `FFFFFFFE` | `FFFFFFFF` | `00000003` | quotient = -2, remainder = -1 |

---

## Что может пойти не так

| Ошибка | Почему плохо | Как правильно |
|---|---|---|
| забыть `cdq` перед `idiv` | `edx:eax` будет мусором | `mov eax,[x]` → `cdq` → `idiv ...` |
| забыть `xor edx, edx` перед `div` | unsigned-делимое будет неправильным | `mov eax,[x]` → `xor edx,edx` → `div ...` |
| писать `idiv eax, ecx` | такой формы нет | делитель один: `idiv ecx` |
| печатать `eax`, когда нужен остаток | остаток лежит в `edx` | `push edx` |
| использовать `div` для отрицательных чисел | `div` — unsigned | `idiv` + `cdq` |
| делить на ноль | runtime crash | проверить условие задачи |

---

## Практика

### A. Trace

Что будет после выполнения?

```asm
mov eax, 17
xor edx, edx
mov ecx, 5
div ecx
```

<details>
<summary>Ответ</summary>

`eax = 3`, `edx = 2`.

</details>

### B. Заполни пропуски

```asm
; signed x / y
mov eax, [x]
___
idiv dword [y]
```

<details>
<summary>Ответ</summary>

```asm
mov eax, [x]
cdq
idiv dword [y]
```

</details>

### C. Напиши сам

Напиши фрагмент для unsigned `x % y`.

<details>
<summary>Ответ</summary>

```asm
mov eax, [x]
xor edx, edx
div dword [y]
; remainder in edx
```

</details>

### D. Найди баг

```asm
mov eax, [x]
idiv dword [y]
push edx
```

Что может быть не так?

<details>
<summary>Ответ</summary>

Перед `idiv` нет `cdq`. В `edx` может быть мусор.

</details>

---

## Чеклист

- [ ] Я помню, что делимое — `edx:eax`.
- [ ] Я могу написать signed division.
- [ ] Я могу написать unsigned division.
- [ ] Я знаю, где частное.
- [ ] Я знаю, где остаток.
- [ ] Я не пишу `idiv eax, ecx`.
- [ ] Я могу объяснить, зачем нужен `cdq`.

## Куда идти дальше: decimal-паттерны

`div/idiv` нужны не только для `a / b`.

Если задача просит палиндромы, дроби, GCD или разворот десятичной записи, смотри [Десятичные алгоритмы](/patterns/decimal).
