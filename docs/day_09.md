# День 09. Деление: `edx:eax`, `div`, `idiv`

> **Важно для вызовов libc.** Перед `call` должно выполняться `esp % 16 == 0`. Выравнивающие байты и аргументы вместе должны занимать число байт, кратное 16. Подробности: [C ABI / CDECL](/c_abi) и [выравнивание стека](/patterns/libc_alignment).

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-06.pdf`: `mul`, `imul`, `div`, `idiv`, пара `edx:eax`, подготовка делимого через `cdq`.

## Входные знания

Перед началом проверь, что ты можешь:

- понимать `movsx`, `movzx` и расширение знака;
- знать, зачем `cdq` формирует `edx:eax`.

Если один из пунктов не получается объяснить или показать на маленьком примере, вернись к [Дню 08](/day_08).

---

## За 30 секунд

- `div` выполняет беззнаковое деление.
- `idiv` выполняет знаковое деление.
- Делимое для 32-битного деления лежит в `edx:eax`.
- Делитель — один явный операнд.
- Частное после деления лежит в `eax`.
- Остаток после деления лежит в `edx`.
- Перед `idiv` обычно нужен `cdq`.
- Перед `div` обычно нужен `xor edx, edx`.

## Минимум после главы

Ты должен уметь:

- написать знаковое `a / b`;
- написать знаковое `a % b`;
- написать беззнаковое `a / b`;
- объяснить, зачем нужен `edx`;
- объяснить, почему забытый `cdq` ломает код;
- не писать несуществующее `idiv eax, ecx`.

Можно пока не заучивать:

- все формы `mul/imul`;
- подробности переполнения при полном 64-битном умножении;
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

### Знаковое деление

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

### Беззнаковое деление

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

Для 32-битного деления процессор берёт 64-битное делимое из пары `edx:eax`.

Поэтому перед делением надо подготовить обе половины:

| Случай | Как подготовить |
|---|---|
| знаковый `int x` в `eax` | `cdq` |
| беззнаковый `uint32_t x` в `eax` | `xor edx, edx` |

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
    push ebp
    mov ebp, esp
    and esp, -16
    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push a
    push fmtIn
    call scanf
    add esp, 16

    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push b
    push fmtIn
    call scanf
    add esp, 16

    mov eax, [a]
    cdq
    idiv dword [b]

    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push eax
    push fmtOut
    call printf
    add esp, 16

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret
```

Чтобы напечатать остаток, печатай `edx`:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push edx
push fmtOut
call printf
add esp, 16
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
| после `mov eax, -7` | `FFFFFFF9` | ? | ? | `eax = -7` |
| после `cdq` | `FFFFFFF9` | `FFFFFFFF` | ? | `edx:eax = -7` |
| после `mov ecx, 3` | `FFFFFFF9` | `FFFFFFFF` | `00000003` | делитель = 3 |
| после `idiv ecx` | `FFFFFFFE` | `FFFFFFFF` | `00000003` | частное = -2, остаток = -1 |

---

## Что может пойти не так

| Ошибка | Почему плохо | Как правильно |
|---|---|---|
| забыть `cdq` перед `idiv` | `edx:eax` будет мусором | `mov eax,[x]` → `cdq` → `idiv ...` |
| забыть `xor edx, edx` перед `div` | беззнаковое делимое будет неправильным | `mov eax,[x]` → `xor edx,edx` → `div ...` |
| писать `idiv eax, ecx` | такой формы нет | делитель один: `idiv ecx` |
| печатать `eax`, когда нужен остаток | остаток лежит в `edx` | `push edx` |
| использовать `div` для отрицательных чисел | `div` работает без знака | `idiv` + `cdq` |
| делить на ноль | программа завершится с ошибкой | проверить условие задачи |

---

<a id="idiv-overflow"></a>
## Граница знакового деления: `INT32_MIN / -1`

`cdq` и ненулевой делитель не гарантируют успешный `idiv`. Для делимого `INT32_MIN` и делителя `-1` математическое частное равно `2147483648`, но оно не помещается в `eax` как `int32_t`; процессор возбуждает divide exception (`#DE`).

Перед `idiv` проверяй два независимых условия:

1. делитель не равен нулю;
2. пара `(eax, divisor)` не равна `(INT32_MIN, -1)`.

<a id="negative-fixture"></a>
### Negative fixture

Negative fixture: `examples/11_idiv_overflow_negative.asm` обязан завершаться ожидаемым `SIGFPE`/divide exception, а не считаться успешным вычислением.

## Практика

### A. Трассировка

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

Напиши фрагмент для беззнакового `x % y`.

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
- [ ] Я могу написать знаковое деление.
- [ ] Я могу написать беззнаковое деление.
- [ ] Я знаю, где частное.
- [ ] Я знаю, где остаток.
- [ ] Я не пишу `idiv eax, ecx`.
- [ ] Я могу объяснить, зачем нужен `cdq`.

## Куда идти дальше: десятичные алгоритмы

`div/idiv` нужны не только для `a / b`.

Если задача просит палиндромы, дроби, наибольший общий делитель или разворот десятичной записи, смотри [Десятичные алгоритмы](/patterns/decimal).

---

## Следующий шаг

1. Реши [TR-09 в рабочей тетради](/transfer_workbook#tr-09) без просмотра ответа.
2. После законченной попытки открой [диагностический ключ TR-09](/transfer_keys#key-tr-09).
3. Запиши нарушенный инвариант и минимальный контрпример в журнал ошибок.
4. Если модель верна — переходи дальше; если нет — вернись к указанной предыдущей теме и затем реши новый вариант.
