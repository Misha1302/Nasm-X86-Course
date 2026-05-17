# День 06. Первая настоящая программа: читаем число и печатаем ответ

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-07.pdf`: базовая NASM-программа, секции, вызовы функций, стековые аргументы.

## Зачем этот день

До этого мы разбирали модель: память, регистры, адреса, секции.

Сегодня NASM наконец становится инструментом для задач: мы научимся читать числа, считать выражение и печатать ответ.

Теорию CDECL подробно разберём в дне 17. Но рабочий шаблон нужен уже сейчас, иначе невозможно сдавать практические задачи.

---

## Главная мысль

`scanf` получает **адрес**, потому что должен куда-то записать число.

`printf` получает **значение**, потому что должен его напечатать.

Аргументы в IA-32 CDECL кладём через `push` справа налево, после вызова чистим стек через `add esp, ...`.

```text
scanf("%d", &x)  -> передаём адрес x
printf("%d", x) -> передаём значение [x]
```

---

## Базовый шаблон программы

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
    push fmtIn          ; "%d"
    call scanf
    add esp, 8

    push dword [x]      ; x
    push fmtOut         ; "%d\n"
    call printf
    add esp, 8

    xor eax, eax
    ret
```

Сейчас это выглядит длинно, но большая часть — boilerplate. Для задач ты будешь менять в основном середину: вычисления между чтением и печатью.

---

## Разбор шаблона по строкам

### Строки формата

```asm
fmtIn db "%d", 0
fmtOut db "%d", 10, 0
```

`%d` — формат для целого числа.

`0` в конце — нулевой байт, конец C-строки.

`10` — символ newline `\n`.

То есть:

```asm
fmtOut db "%d", 10, 0
```

это примерно C-строка:

```c
"%d\n"
```

### Переменная

```asm
x resd 1
```

Резервируем место под один `dword`, то есть 4 байта.

Это похоже на:

```c
int x;
```

### Внешние функции

```asm
extern scanf
extern printf
```

Мы говорим NASM: эти функции есть, но они находятся не в нашем файле. Линковщик найдёт их в libc.

### Точка входа

```asm
global main
```

Мы говорим линковщику: метка `main` должна быть видна снаружи.

---

## Почему порядок `push` такой странный

C:

```c
scanf("%d", &x);
```

Аргументы:

```text
1-й: "%d"
2-й: &x
```

В CDECL они кладутся справа налево:

```asm
push x       ; второй аргумент: &x
push fmtIn   ; первый аргумент: "%d"
call scanf
add esp, 8
```

То же самое с `printf`:

C:

```c
printf("%d\n", x);
```

NASM:

```asm
push dword [x]  ; второй аргумент: x
push fmtOut     ; первый аргумент: "%d\n"
call printf
add esp, 8
```

---

## Как выглядит стек перед `call scanf`

После:

```asm
push x
push fmtIn
```

стек выглядит так:

```text
higher addresses
+----------------+
| x              |  second argument: &x
+----------------+
| fmtIn          |  first argument: "%d"
+----------------+ <- esp
lower addresses
```

Функция `scanf` ожидает, что первый аргумент лежит ближе к `esp`.

После возврата мы делаем:

```asm
add esp, 8
```

и убираем оба аргумента.

---

## Почему после вызова `add esp, 8`

Один `push` в IA-32 кладёт 4 байта.

Мы сделали два `push`:

```text
2 arguments * 4 bytes = 8 bytes
```

Поэтому:

```asm
add esp, 8
```

Если аргументов три:

```asm
add esp, 12
```

Если забыть очистить стек, программа может не упасть сразу, но стек станет неправильным. Позже это приведёт к очень неприятным багам.

---

## Читаем два числа

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

Здесь вычисление — всего две строки:

```asm
mov eax, [a]
add eax, [b]
```

В C++ это:

```cpp
answer = a + b;
```

---

## Читаем несколько чисел одним `scanf`

Можно читать и так:

```c
scanf("%d%d", &a, &b);
```

Тогда строка формата:

```asm
fmt2 db "%d%d", 0
```

Вызов:

```asm
push b
push a
push fmt2
call scanf
add esp, 12
```

Почему `push b`, потом `push a`, потом `push fmt2`?

Потому что аргументы кладутся справа налево:

```text
scanf("%d%d", &a, &b)
             1   2   3
push &b
push &a
push format
```

Для первых задач проще читать по одному числу, но полезно знать оба варианта.

---

## Печатаем значение из регистра

Если ответ уже в `eax`, можно сделать:

```asm
push eax
push fmtOut
call printf
add esp, 8
```

Не обязательно сначала сохранять ответ в память.

Но если ты хочешь сохранить:

```asm
mov [ans], eax
```

а потом напечатать:

```asm
push dword [ans]
push fmtOut
call printf
add esp, 8
```

---

## Скелет для задач

Вот шаблон, который можно реально копировать и менять:

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

## Мини-челленджи

### 1. Ввод `x`, вывод `x`

Сделай программу, которая читает одно число и печатает его.

<details>
<summary>Главная идея</summary>

```asm
push x
push fmtIn
call scanf
add esp, 8

push dword [x]
push fmtOut
call printf
add esp, 8
```

</details>

### 2. Ввод `a b`, вывод `a+b`

<details>
<summary>Главная идея</summary>

После чтения:

```asm
mov eax, [a]
add eax, [b]
```

Потом печатаем `eax`.

</details>

### 3. Ввод `a b c`, вывод `a*b+c`

<details>
<summary>Главная идея</summary>

```asm
mov eax, [a]
imul eax, [b]
add eax, [c]
```

</details>

### 4. Почему `scanf` получает `x`, а `printf` — `[x]`?

<details>
<summary>Ответ</summary>

`scanf` должен записать число, значит нужен адрес. `printf` должен напечатать число, значит нужно значение.

</details>

---

## Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| `push [x]` для `scanf` | передаёшь значение вместо адреса |
| `push [fmtIn]` | строка формата нужна адресом |
| забыть `add esp, 8` | стек становится несбалансированным |
| перепутать порядок аргументов | CDECL кладёт справа налево |
| печатать `[x]`, когда ответ в `eax` | можно печатать `eax` напрямую |
| не указать `dword` | NASM может не понять размер памяти |

---

## Что должно остаться в голове

После этого дня ты должен уметь:

- написать программу с `scanf` и `printf`;
- объяснить, почему `scanf` получает адрес;
- объяснить, почему `printf` получает значение;
- правильно сделать `push` аргументов;
- посчитать, сколько байт убрать через `add esp, ...`;
- прочитать 2–3 числа и вывести арифметический ответ.

Это первый день, после которого NASM уже можно использовать для простых задач.
