# Карточки ошибок NASM

> **Важно для вызовов libc.** Перед `call` должно выполняться `esp % 16 == 0`. Выравнивающие байты и аргументы вместе должны занимать число байт, кратное 16. Подробности: [C ABI / CDECL](/c_abi) и [выравнивание стека](/patterns/libc_alignment).

Эта страница — не теория, а быстрый отладочный справочник. Открой её, когда программа собирается, но ведёт себя странно.

## `scanf` падает или пишет в странное место

Симптом:

```text
Segmentation fault после scanf
```

Плохой код:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push dword [x]
push fmtIn
call scanf
add esp, 16
```

Причина:

`scanf` ждёт адрес, а `[x]` — это значение.

Правильно:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push x
push fmtIn
call scanf
add esp, 16
```

---

## `printf` печатает странное число

Плохой код:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push x
push fmtOut
call printf
add esp, 16
```

Причина:

Для `printf("%d", x)` нужно значение, а `x` — адрес.

Правильно:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push dword [x]
push fmtOut
call printf
add esp, 16
```

Если ответ уже в `eax`:

```asm
sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push eax
push fmtOut
call printf
add esp, 16
```

---

## После `printf` значение в `eax` исчезло

Плохой код:

```asm
mov eax, [answer]

sub esp, 8       ; padding: 8 + 8 argument bytes = 16
push eax
push fmtOut
call printf
add esp, 16

add eax, 1       ; здесь eax уже может быть не answer
```

Причина:

`printf` имеет право изменить `eax`, `ecx` и `edx`.

Варианты исправления:

```asm
; вариант 1: перечитать из памяти
mov eax, [answer]
add eax, 1
```

```asm
; вариант 2: сохранить значение
push eax
sub esp, 4       ; saved dword + 4 padding + 8 argument bytes = 16
push eax
push fmtOut
call printf
add esp, 12
pop eax
```

---

## Деление даёт мусор или падает

Плохой код знакового деления:

```asm
mov eax, [x]
idiv dword [y]
```

Причина:

`idiv` делит `edx:eax`, а `edx` не подготовлен.

Правильно:

```asm
mov eax, [x]
cdq
idiv dword [y]
```

---

## Беззнаковое деление работает неправильно

Плохой код:

```asm
mov eax, [x]
div dword [y]
```

Причина:

`div` тоже делит `edx:eax`. Для обычного 32-битного беззнакового `x` верхняя половина должна быть нулём.

Правильно:

```asm
mov eax, [x]
xor edx, edx
div dword [y]
```

---

## Нужен остаток, но печатается частное

После деления:

```text
eax = quotient
edx = remainder
```

Печать частного:

```asm
push eax
```

Печать остатка:

```asm
push edx
```

---

## Модуль без переходов неправильно работает для отрицательных чисел

Плохой код:

```asm
mov eax, [x]
mov edx, eax
shr edx, 31
xor eax, edx
sub eax, edx
```

Причина:

`shr` даёт `0` или `1`. Для вычисления модуля без переходов нужна маска `0` или `FFFFFFFFh`.

Правильно:

```asm
mov eax, [x]
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
```

---

## Перепутаны знаковое и беззнаковое сравнения

Один и тот же битовый набор может иметь разный смысл:

```text
0xFFFFFFFF = -1 as signed
0xFFFFFFFF = 4294967295 as unsigned
```

| Смысл в C | Переход |
|---|---|
| знаковое `<` | `jl` |
| знаковое `<=` | `jle` |
| знаковое `>` | `jg` |
| знаковое `>=` | `jge` |
| беззнаковое `<` | `jb` |
| беззнаковое `<=` | `jbe` |
| беззнаковое `>` | `ja` |
| беззнаковое `>=` | `jae` |

---

## Переход смотрит не на тот `cmp`

Плохой код:

```asm
cmp eax, ebx
add ecx, 1
jl .less
```

Причина:

`add` изменил флаги. `jl` уже смотрит не на `cmp eax, ebx`.

Правильно:

```asm
cmp eax, ebx
jl .less
add ecx, 1
```

---

## Первый аргумент функции перепутан

Карта фрейма:

```text
[ebp+12]  argument 2
[ebp+8]   argument 1
[ebp+4]   return address
[ebp]     old ebp
[ebp-4]   local variable 1
```

Ошибка:

```asm
mov eax, [ebp+4]   ; это return address, не первый аргумент
```

Правильно:

```asm
mov eax, [ebp+8]
```

---

## Использовал `ebx`, `esi`, `edi` и не восстановил

В CDECL:

| Регистр | Кто сохраняет |
|---|---|
| `eax`, `ecx`, `edx` | вызывающая функция, если значения нужны после вызова |
| `ebx`, `esi`, `edi`, `ebp` | вызываемая функция |

Если функция использует `ebx`, нужно сохранить и восстановить:

```asm
my_func:
    push ebp
    mov ebp, esp
    push ebx

    ; use ebx

    pop ebx
    pop ebp
    ret
```

---

## `push [fmt]` вместо `push fmt`

Плохой код:

```asm
push dword [fmtOut]
call printf
```

Причина:

`fmtOut` — адрес строки. `[fmtOut]` — первые 4 байта строки, прочитанные как число.

Правильно:

```asm
push fmtOut
call printf
```

---

## `printf("%f")` получил 4 байта вместо 8

`printf("%f")` ждёт `double`, то есть 8 байт.

Правильно для x87:

```asm
sub esp, 12      ; 4 bytes padding + 8-byte double
fstp qword [esp]
push fmtFloat
call printf
add esp, 16
```

Почему `12`?

```text
8 bytes double + 4 bytes format pointer
```

## Маска `0/1` вместо `0/-1`

Симптом: выбор без переходов меняет только младший бит.

Плохо:

```text
mask = 1
answer = (a & mask) | (b & ~mask)
```

Нужно:

```text
mask = 00000000h или FFFFFFFFh
```

---

## Стек не выровнен перед libc

Симптом: локально работает, а в Spring-04 падает или не принимается.

Причина: в условии может быть явно указано 16-байтное выравнивание стека.

Что делать: вызывать libc через аккуратные вспомогательные функции и проверять `esp`.

---

## Рекурсия потеряла значение после `call`

Плохо:

```asm
mov eax, [ebp+8]
call func
; ожидать, что eax всё ещё старое значение
```

Вызываемая функция может изменить `eax`. Сохрани значение в локальную переменную или в регистр, который она обязана сохранять.

---

## Большой результат обрезался до `eax`

Если задача требует число больше 32 бит, `eax` хранит только младшие 32 бита.

Для 64-битного результата нужна пара `edx:eax`, для ещё большего — арифметика над несколькими машинными словами.
