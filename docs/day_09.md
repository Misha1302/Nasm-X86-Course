# День 09. Почему деление в x86 такое странное

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-06.pdf`: `mul`, `imul`, `div`, `idiv`, пара `edx:eax`, подготовка делимого через `cdq`.

## Зачем этот день

В C++ ты пишешь просто:

```cpp
q = x / y;
r = x % y;
```

В x86 это не одна красивая операция с двумя обычными аргументами. Деление завязано на конкретные регистры:

```text
edx:eax / operand
```

Сначала это раздражает. Но если запомнить схему, деление становится вполне механическим.

---

## Главная мысль

Для 32-битного деления:

```text
делимое  = edx:eax
делитель = явный операнд команды
частное  = eax
остаток  = edx
```

Картинка:

```text
Before division:

+----------------+----------------+
|      edx       |      eax       |
+----------------+----------------+
   high 32 bits      low 32 bits

idiv ecx

After division:

eax = quotient
edx = remainder
```

---

## Почему вообще `edx:eax`

Если делим 32-битные числа, делимое может быть шире 32 бит.

Например, после умножения двух 32-битных чисел результат может занимать 64 бита. Поэтому исторически x86 использует пару регистров:

```text
edx:eax
```

`edx` — старшая половина.

`eax` — младшая половина.

---

## Умножение: `mul` и `imul`

### Удобная форма `imul`

Чаще всего в учебных задачах удобно писать так:

```asm
imul eax, ebx        ; eax = eax * ebx
imul eax, ebx, 41    ; eax = ebx * 41
```

Это похоже на обычные выражения C++.

Пример:

```asm
mov eax, [x]
imul eax, 41
```

C++-смысл:

```cpp
x * 41
```

### Историческая форма

Есть форма, где результат попадает в `edx:eax`:

```asm
mul ebx    ; unsigned: edx:eax = eax * ebx
imul ebx   ; signed:   edx:eax = eax * ebx
```

То есть `eax` участвует неявно.

Для первых домашних чаще хватает удобной формы `imul eax, ..., ...`.

---

## Деление: `div` и `idiv`

| Команда | Смысл |
|---|---|
| `div` | unsigned division |
| `idiv` | signed division |

У команды один явный операнд — делитель.

Плохо:

```asm
idiv eax, ecx ; такой формы нет
```

Хорошо:

```asm
mov eax, [x]
cdq
idiv ecx
```

Здесь делимое — неявно `edx:eax`, делитель — `ecx`.

---

## Signed division: почти всегда `cdq` перед `idiv`

Шаблон:

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

Что делает `cdq`?

```text
если eax >= 0 -> edx = 00000000h
если eax < 0  -> edx = FFFFFFFFh
```

Так `eax` превращается в правильное 64-битное signed-делимое `edx:eax`.

Пример для `x = -7`:

```text
eax = FFFFFFF9
edx = FFFFFFFF
edx:eax = FFFFFFFFFFFFFFF9 = -7 как 64-bit signed
```

---

## Unsigned division: обычно `xor edx, edx` перед `div`

Шаблон:

```asm
mov eax, [x]
xor edx, edx
div dword [y]
; eax = x / y
; edx = x % y
```

Почему `xor edx, edx`?

Потому что для обычного 32-битного unsigned `x` старшая половина делимого должна быть нулём:

```text
edx:eax = 00000000:x
```

---

## Где лежит остаток

После деления:

```text
eax = quotient
edx = remainder
```

C++:

```cpp
q = x / y;
r = x % y;
```

NASM:

```asm
mov eax, [x]
cdq
idiv dword [y]

; eax is q
; edx is r
```

Если надо напечатать частное:

```asm
push eax
```

Если надо напечатать остаток:

```asm
push edx
```

---

## Что может пойти не так

### 1. Забыли подготовить `edx`

Плохо:

```asm
mov eax, [x]
idiv dword [y]
```

В `edx` мог быть мусор. Процессор будет делить не `x`, а `edx:eax`.

### 2. Деление на ноль

```asm
idiv dword [y]
```

Если `y = 0`, программа упадёт с ошибкой деления.

### 3. Частное не помещается

`idiv` может упасть, если результат не помещается в `eax`.

Классический signed-пример:

```text
INT_MIN / -1
```

Математически получится `2147483648`, но это не помещается в signed 32-bit.

---

## Полная программа: частное `a / b`

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

---

## Полная программа: остаток `a % b`

Отличается только печатью `edx`:

```asm
mov eax, [a]
cdq
idiv dword [b]

push edx
push fmtOut
call printf
add esp, 8
```

---

## Маленький пример: `(a*b+c)/10`

```asm
mov eax, [a]
imul eax, [b]
add eax, [c]
cdq
mov ecx, 10
idiv ecx
```

После этого:

```text
eax = (a*b+c)/10
edx = (a*b+c)%10
```

---

## Мини-челленджи

### 1. Signed `a / b`

Напиши фрагмент.

<details>
<summary>Ответ</summary>

```asm
mov eax, [a]
cdq
idiv dword [b]
```

Частное в `eax`.

</details>

### 2. Unsigned `a % b`

Напиши фрагмент.

<details>
<summary>Ответ</summary>

```asm
mov eax, [a]
xor edx, edx
div dword [b]
```

Остаток в `edx`.

</details>

### 3. Что делает `cdq`?

<details>
<summary>Ответ</summary>

Расширяет знак `eax` в `edx:eax`: для положительного `edx=0`, для отрицательного `edx=FFFFFFFFh`.

</details>

### 4. Почему нельзя `idiv eax, ecx`?

<details>
<summary>Ответ</summary>

У `idiv` делимое неявно лежит в `edx:eax`, а явный операнд только один — делитель.

</details>

### 5. Где остаток?

<details>
<summary>Ответ</summary>

В `edx`.

</details>

---

## Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| забыть `cdq` перед `idiv` | `edx:eax` будет неправильным |
| забыть `xor edx, edx` перед `div` | unsigned-делимое будет неправильным |
| писать `idiv eax, ecx` | такой формы команды нет |
| печатать `eax`, когда нужен остаток | остаток лежит в `edx` |
| использовать `div` для отрицательных чисел | `div` — unsigned |
| делить на ноль | runtime crash |

---

## Что должно остаться в голове

После этого дня ты должен уметь:

- объяснить пару `edx:eax`;
- написать signed division через `cdq` + `idiv`;
- написать unsigned division через `xor edx, edx` + `div`;
- помнить, что частное в `eax`, остаток в `edx`;
- не писать несуществующую форму `idiv eax, ecx`;
- понимать, почему деление сложнее сложения.

Если можешь по памяти написать шаблон `a / b` и `a % b`, день закрыт.
