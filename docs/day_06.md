# День 06. `scanf`, `printf` и первая настоящая программа

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-07.pdf`: базовая NASM-программа, секции, вызовы функций, стековые аргументы.

## За 30 секунд

- `scanf` получает адрес, потому что записывает значение.
- `printf` получает значение, потому что печатает его.
- В IA-32 CDECL аргументы кладутся через `push` справа налево.
- После вызова caller чистит стек: `add esp, argument_count * 4`.
- Ответ часто удобно держать в `eax` и сразу печатать.
- Не рассчитывай на сохранность `eax`, `ecx`, `edx` после `printf` / `scanf`.

## Минимум после главы

Ты должен уметь:

- прочитать одно число;
- прочитать два-три числа;
- напечатать значение переменной;
- напечатать результат из `eax`;
- посчитать, сколько байт убрать из стека;
- найти ошибки `push [x]` для `scanf` и `push x` для `printf`.

Можно пока не заучивать:

- все детали CDECL;
- frame layout через `[ebp+8]`;
- stack alignment.

Подробный CDECL будет в [дне 17](/day_17) и на странице [C ABI / CDECL](/c_abi).

---

## Главная таблица

| C | NASM | Почему |
|---|---|---|
| `scanf("%d", &x)` | `push x` | нужен адрес |
| `printf("%d", x)` | `push dword [x]` | нужно значение |
| `printf("%d", eax)` | `push eax` | ответ уже в регистре |

---

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
    push x
    push fmtIn
    call scanf
    add esp, 8

    push dword [x]
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

---

## Почему порядок `push` справа налево

C:

```c
printf("%d\n", x);
```

Аргументы:

```text
1: format string
2: x
```

CDECL кладёт их справа налево:

```asm
push dword [x]      ; second argument
push fmtOut         ; first argument
call printf
add esp, 8
```

Перед `call` стек выглядит так:

```text
higher addresses
+----------------+
| x              | second argument
+----------------+
| fmtOut         | first argument <- esp
+----------------+
lower addresses
```

---

## Почему после вызова `add esp, 8`

Один `push` в IA-32 кладёт 4 байта.

```text
2 arguments * 4 bytes = 8 bytes
```

Поэтому:

```asm
add esp, 8
```

Для трёх аргументов:

```asm
add esp, 12
```

---

## Читаем два числа по одному

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
    add eax, [b]

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

Главная часть вычисления:

```asm
mov eax, [a]
add eax, [b]
```

C++-смысл:

```cpp
answer = a + b;
```

---

## Читаем несколько чисел одним `scanf`

C:

```c
scanf("%d%d", &a, &b);
```

NASM:

```asm
fmt2 db "%d%d", 0

push b
push a
push fmt2
call scanf
add esp, 12
```

Почему `push b`, потом `push a`, потом `push fmt2`?

Потому что аргументы кладутся справа налево.

---

## Печать из регистра

Если ответ уже в `eax`, не надо сохранять его в память:

```asm
push eax
push fmtOut
call printf
add esp, 8
```

Но после `printf` нельзя считать, что `eax` всё ещё содержит ответ. `printf` имеет право испортить `eax`.

---

## Скелет для задач

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
    ; read a
    push a
    push fmtIn
    call scanf
    add esp, 8

    ; read b
    push b
    push fmtIn
    call scanf
    add esp, 8

    ; compute answer in eax
    mov eax, [a]
    add eax, [b]

    ; print eax
    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

---

## Частые ошибки

| Ошибка | Почему плохо | Как правильно |
|---|---|---|
| `push [x]` для `scanf` | передаёшь значение вместо адреса | `push x` |
| `push [fmtIn]` | строка формата нужна адресом | `push fmtIn` |
| забыть `add esp, 8` | стек становится несбалансированным | убрать аргументы после `call` |
| перепутать порядок аргументов | CDECL кладёт справа налево | сначала последний аргумент |
| считать, что `eax` сохранился после `printf` | `eax` caller-saved | перечитать/сохранить значение |
| не указать `dword` | NASM может не понять размер памяти | `push dword [x]` |

---

## Практика

### A. Trace

После этих строк что лежит на стеке перед `call`?

```asm
push dword [x]
push fmtOut
call printf
```

<details>
<summary>Ответ</summary>

Ближе к `esp` лежит `fmtOut`, выше — значение `[x]`.

</details>

### B. Заполни пропуски

```asm
; printf("%d\n", x)
push dword ___
push ___
call printf
add esp, ___
```

<details>
<summary>Ответ</summary>

```asm
push dword [x]
push fmtOut
call printf
add esp, 8
```

</details>

### C. Напиши сам

Прочитай `a`, `b`, напечатай `a*b+10`.

<details>
<summary>Главная часть</summary>

```asm
mov eax, [a]
imul eax, [b]
add eax, 10

push eax
push fmtOut
call printf
add esp, 8
```

</details>

### D. Найди баг

```asm
mov eax, [answer]

push eax
push fmtOut
call printf
add esp, 8

add eax, 1
```

Что не так?

<details>
<summary>Ответ</summary>

После `printf` регистр `eax` может быть испорчен. Если значение нужно дальше, его надо сохранить или перечитать.

</details>

---

## Чеклист

- [ ] Я могу написать программу “ввод x, вывод x”.
- [ ] Я могу прочитать два числа.
- [ ] Я могу напечатать ответ из `eax`.
- [ ] Я понимаю, почему `scanf` получает `x`.
- [ ] Я понимаю, почему `printf` получает `[x]`.
- [ ] Я умею посчитать `add esp, ...` после вызова.
