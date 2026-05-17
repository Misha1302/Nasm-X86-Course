# Карточки ошибок NASM

Эта страница — не теория, а быстрый отладочный справочник. Открой её, когда программа собирается, но ведёт себя странно.

## `scanf` падает или пишет в странное место

Симптом:

```text
Segmentation fault после scanf
```

Плохой код:

```asm
push dword [x]
push fmtIn
call scanf
add esp, 8
```

Причина:

`scanf` ждёт адрес, а `[x]` — это значение.

Правильно:

```asm
push x
push fmtIn
call scanf
add esp, 8
```

---

## `printf` печатает странное число

Плохой код:

```asm
push x
push fmtOut
call printf
add esp, 8
```

Причина:

Для `printf("%d", x)` нужно значение, а `x` — адрес.

Правильно:

```asm
push dword [x]
push fmtOut
call printf
add esp, 8
```

Если ответ уже в `eax`:

```asm
push eax
push fmtOut
call printf
add esp, 8
```

---

## После `printf` значение в `eax` исчезло

Плохой код:

```asm
mov eax, [answer]

push eax
push fmtOut
call printf
add esp, 8

add eax, 1       ; здесь eax уже может быть не answer
```

Причина:

`eax`, `ecx`, `edx` — caller-saved. `printf` имеет право их испортить.

Варианты исправления:

```asm
; вариант 1: перечитать из памяти
mov eax, [answer]
add eax, 1
```

```asm
; вариант 2: сохранить значение
push eax
push eax
push fmtOut
call printf
add esp, 8
pop eax
```

---

## Деление даёт мусор или падает

Плохой signed-код:

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

## Unsigned division работает неправильно

Плохой код:

```asm
mov eax, [x]
div dword [y]
```

Причина:

`div` тоже делит `edx:eax`. Для обычного 32-битного unsigned `x` верхняя половина должна быть нулём.

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

## Branchless abs неправильно работает для отрицательных

Плохой код:

```asm
mov eax, [x]
mov edx, eax
shr edx, 31
xor eax, edx
sub eax, edx
```

Причина:

`shr` даёт `0` или `1`. Для branchless abs нужна маска `0` или `FFFFFFFFh`.

Правильно:

```asm
mov eax, [x]
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
```

---

## Signed и unsigned comparison перепутаны

Один и тот же битовый набор может иметь разный смысл:

```text
0xFFFFFFFF = -1 as signed
0xFFFFFFFF = 4294967295 as unsigned
```

| C-смысл | Jump |
|---|---|
| signed `<` | `jl` |
| signed `<=` | `jle` |
| signed `>` | `jg` |
| signed `>=` | `jge` |
| unsigned `<` | `jb` |
| unsigned `<=` | `jbe` |
| unsigned `>` | `ja` |
| unsigned `>=` | `jae` |

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
| `eax`, `ecx`, `edx` | caller, если нужно |
| `ebx`, `esi`, `edi`, `ebp` | callee |

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
sub esp, 8
fstp qword [esp]
push fmtFloat
call printf
add esp, 12
```

Почему `12`?

```text
8 bytes double + 4 bytes format pointer
```

## Маска `0/1` вместо `0/-1`

Симптом: branchless select выбирает только младший бит.

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

Причина: в условии может быть явно сказано про 16-byte stack alignment.

Что делать: вызывать libc через аккуратные wrapper-функции и проверять `esp`.

---

## Рекурсия потеряла значение после `call`

Плохо:

```asm
mov eax, [ebp+8]
call func
; ожидать, что eax всё ещё старое значение
```

`eax` caller-saved. Сохрани значение в локальную переменную или callee-saved регистр.

---

## Большой результат обрезался до `eax`

Если задача требует число больше 32 бит, `eax` хранит только младшие 32 бита.

Для 64-bit нужен `edx:eax`, для ещё большего результата — multiword arithmetic.
