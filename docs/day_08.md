# День 08. Как один байт становится `255` или `-1`

## Опора на материалы ВШЭ

`Slides2026-03.pdf`, `Slides2026-04.pdf`: `movsx`, `movzx`, `cbw`, `cwd`, `cdq`, знаковое расширение и подготовка к `idiv`.

## Зачем этот день

В C++ ты привык, что тип многое решает:

```cpp
signed char a = -1;
unsigned char b = 255;
```

Но на уровне битов это может быть одно и то же:

```text
11111111
```

Ассемблеру надо явно сказать, как маленькое значение превращать в большое: как signed или как unsigned.

Сегодня разбираем команды, которые делают это правильно:

```asm
movsx
movzx
cbw
cwd
cdq
```

---

## Главная мысль

`movzx` расширяет нулями.

`movsx` расширяет знаковым битом.

`cdq` расширяет знак `eax` в пару `edx:eax` перед signed-делением.

---

## Один байт, два смысла

Пусть в памяти лежит байт:

```text
0xFF = 11111111
```

Как unsigned 8-bit это:

```text
255
```

Как signed 8-bit это:

```text
-1
```

Биты одни и те же. Разная только интерпретация.

---

## Zero extension: `movzx`

```asm
movzx eax, byte [x]
```

Если:

```text
[x] = 0xFF
```

то после `movzx`:

```text
eax = 0x000000FF = 255
```

Картинка:

```text
source byte:
11111111

zero-extended dword:
00000000 00000000 00000000 11111111
```

То есть сверху просто добавили нули.

C++-аналогия:

```cpp
unsigned char x = 0xFF;
int y = x; // 255
```

---

## Sign extension: `movsx`

```asm
movsx eax, byte [x]
```

Если:

```text
[x] = 0xFF
```

то после `movsx`:

```text
eax = 0xFFFFFFFF = -1
```

Картинка:

```text
source byte:
11111111

sign-extended dword:
11111111 11111111 11111111 11111111
```

Почему добавились единицы?

Потому что старший бит исходного байта равен `1`. Для signed-числа это знак минуса. Расширение должно сохранить значение, поэтому знак “размножается”.

C++-аналогия:

```cpp
signed char x = -1;
int y = x; // -1
```

---

## Пример с `0x80`

Байт:

```text
0x80 = 10000000
```

Unsigned:

```text
128
```

Signed 8-bit:

```text
-128
```

`movzx`:

```text
00000000 00000000 00000000 10000000 = 128
```

`movsx`:

```text
11111111 11111111 11111111 10000000 = -128
```

Это один из лучших тестов на понимание темы.

---

## `movsx` и `movzx` с разными размерами

Примеры:

```asm
movsx eax, byte [x]   ; signed byte -> dword
movsx eax, word [x]   ; signed word -> dword

movzx eax, byte [x]   ; unsigned byte -> dword
movzx eax, word [x]   ; unsigned word -> dword
```

Важно: нельзя сделать `movzx` из 32 бит в 32 бита — расширять нечего.

---

## Зачем вообще это нужно

Представь C++:

```cpp
signed char c = -5;
int x = c + 10;
```

Перед сложением `c` надо расширить до `int` как signed.

Ассемблерная идея:

```asm
movsx eax, byte [c]
add eax, 10
```

А если:

```cpp
unsigned char c = 250;
int x = c + 10;
```

то нужно:

```asm
movzx eax, byte [c]
add eax, 10
```

Если перепутать `movsx` и `movzx`, результат может стать совсем другим.

---

## `cbw`, `cwd`, `cdq`

Это старые короткие команды знакового расширения.

| Команда | Что делает |
|---|---|
| `cbw` | `AL -> AX`, sign extension |
| `cwd` | `AX -> DX:AX`, sign extension |
| `cdq` | `EAX -> EDX:EAX`, sign extension |

Самая важная для нас:

```asm
cdq
```

Она смотрит на знак `eax`:

- если `eax >= 0`, делает `edx = 0`;
- если `eax < 0`, делает `edx = 0xFFFFFFFF`.

Зачем? Для signed division.

---

## Почему `cdq` нужен перед `idiv`

`idiv` делит не просто `eax`.

Он делит пару:

```text
edx:eax
```

То есть 64-битное signed-делимое, где `edx` — старшая часть, `eax` — младшая.

Если у нас есть 32-битное число в `eax`, перед `idiv` нужно правильно расширить его до `edx:eax`.

```asm
mov eax, [x]
cdq
idiv dword [y]
```

Если `x = 7`:

```text
eax = 00000007
edx = 00000000
```

Если `x = -7`:

```text
eax = FFFFFFF9
edx = FFFFFFFF
```

Так пара `edx:eax` действительно означает `-7` как 64-битное signed-число.

---

## Что будет, если забыть `cdq`

Плохо:

```asm
mov eax, [x]
idiv dword [y]
```

Почему плохо?

Потому что в `edx` может лежать старый мусор от предыдущих операций.

`idiv` будет делить не `x`, а непонятное число `edx:eax`.

Иногда программа просто упадёт с division error.

---

## Мини-пример: signed division

```asm
section .data
    fmtIn db "%d", 0
    fmtOut db "%d", 10, 0

section .bss
    x resd 1
    y resd 1

section .text
    extern scanf
    extern printf
    global main

main:
    push x
    push fmtIn
    call scanf
    add esp, 8

    push y
    push fmtIn
    call scanf
    add esp, 8

    mov eax, [x]
    cdq
    idiv dword [y]

    push eax        ; quotient
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

Чтобы напечатать остаток, надо печатать `edx`, а не `eax`.

---

## Мини-челленджи

### 1. `movzx` для `0x80`

Что будет?

<details>
<summary>Ответ</summary>

```text
0x00000080 = 128
```

</details>

### 2. `movsx` для `0x80`

Что будет?

<details>
<summary>Ответ</summary>

```text
0xFFFFFF80 = -128
```

</details>

### 3. `movzx` против `movsx` для `0xFF`

<details>
<summary>Ответ</summary>

`movzx` даст `0x000000FF = 255`.

`movsx` даст `0xFFFFFFFF = -1`.

</details>

### 4. Что делает `cdq`, если `eax` положительный?

<details>
<summary>Ответ</summary>

`edx = 0`.

</details>

### 5. Что делает `cdq`, если `eax` отрицательный?

<details>
<summary>Ответ</summary>

`edx = 0xFFFFFFFF`.

</details>

---

## Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| использовать `movzx` для signed char | отрицательное число станет большим положительным |
| использовать `movsx` для unsigned char | числа `128..255` станут отрицательными |
| забыть `cdq` перед `idiv` | `edx:eax` будет неправильным |
| думать, что `0xFF` само знает свой знак | знак задаётся интерпретацией |
| печатать `eax`, когда нужен остаток | остаток после `idiv` лежит в `edx` |

---

## Что должно остаться в голове

После этого дня ты должен уметь:

- объяснить разницу `movsx` и `movzx`;
- вручную расширить `0x80` и `0xFF`;
- понять, почему signed/unsigned — это интерпретация битов;
- объяснить, зачем нужен `cdq`;
- написать шаблон signed-деления.

Если ты можешь объяснить, почему `0xFF` бывает и `255`, и `-1`, тема усвоена.
