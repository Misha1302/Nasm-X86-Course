# День 06. `scanf`, `printf` и первая настоящая программа

> **ABI-условие для libc.** Перед первым полным фрагментом с `printf`/`scanf` тело функции должно получить `esp % 16 == 0`, например через `push ebp; mov ebp, esp; and esp, -16`. Padding и аргументы вместе занимают кратное 16 число байт; полный вывод находится в [C ABI / CDECL](/c_abi) и [паттерне выравнивания](/patterns/libc_alignment).

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-07.pdf`: базовая NASM-программа, секции, вызовы функций, стековые аргументы.

## Входные знания

Перед началом проверь, что ты можешь:

- отличать адрес `x` от значения `[x]`;
- понимать секции `.data`, `.bss`, `.text`;
- знать, что `push` временно кладёт 4 байта в стек; точная модель будет в днях 16–17.

Если один из пунктов не получается объяснить или показать на маленьком примере, вернись к [Дню 05](/day_05).

---

## ABI-инвариант: выравнивание перед `call`

В современной GNU/Linux i386-среде одного порядка `push` и cleanup недостаточно. В полном `main` сначала создаём выровненное тело:

```asm
main:
    push ebp
    mov ebp, esp
    and esp, -16
```

После этого перед каждым внешним `call` padding и аргументы вместе должны занимать кратное 16 число байт. Для двух 32-bit аргументов: `sub esp,8`, два `push`, `call`, `add esp,16`. Для трёх: `sub esp,4`, три `push`, cleanup 16. Эпилог: `mov esp,ebp; pop ebp; ret`.

Короткий шаблон без этого frame считается только схемой порядка аргументов, а не полной ABI-корректной программой.

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

## Временная модель вызова

В этой главе стек нужен только как рабочая модель для ввода и вывода. Не пытайся пока запомнить весь CDECL как набор магических правил.

```text
push аргументов справа налево
        ↓
call кладёт адрес возврата и передаёт управление
        ↓
функция работает и делает ret
        ↓
caller убирает ранее положенные аргументы
```

Отсюда следует `add esp, 8` после двух аргументов. В [дне 16](/day_16) мы разберём точную механику `push/call/ret`, а в [дне 17](/day_17) построим полный frame layout и объясним ответственность caller/callee.

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
    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push x
    push fmtIn
    call scanf
    add esp, 16

    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push dword [x]
    push fmtOut
    call printf
    add esp, 16

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
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push dword [x]      ; second argument
push fmtOut         ; first argument
call printf
add esp, 16
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
    add eax, [b]

    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push eax
    push fmtOut
    call printf
    add esp, 16

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

sub esp, 4       ; padding: 4 + 12 argument bytes = 16
push b
push a
push fmt2
call scanf
add esp, 16
```

Почему `push b`, потом `push a`, потом `push fmt2`?

Потому что аргументы кладутся справа налево.

---

## Печать из регистра

Если ответ уже в `eax`, не надо сохранять его в память:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push eax
push fmtOut
call printf
add esp, 16
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
    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push a
    push fmtIn
    call scanf
    add esp, 16

    ; read b
    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push b
    push fmtIn
    call scanf
    add esp, 16

    ; compute answer in eax
    mov eax, [a]
    add eax, [b]

    ; print eax
    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push eax
    push fmtOut
    call printf
    add esp, 16

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
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push dword [x]
push fmtOut
call printf
add esp, 16
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

sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push eax
push fmtOut
call printf
add esp, 16
```

</details>

### D. Найди баг

```asm
mov eax, [answer]

sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push eax
push fmtOut
call printf
add esp, 16

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

---

## Следующий шаг

1. Реши [TR-06 в рабочей тетради](/transfer_workbook#tr-06) без просмотра ответа.
2. После законченной попытки открой [диагностический ключ TR-06](/transfer_keys#key-tr-06).
3. Запиши нарушенный инвариант и минимальный контрпример в журнал ошибок.
4. Если модель верна — переходи дальше; если нет — вернись к указанному prerequisite и затем реши новый вариант.
