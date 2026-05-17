# День 05. `x` и `[x]`: адрес против значения

## Опора на материалы ВШЭ

`Slides2026-02.pdf`, `Slides2026-04.pdf`: память, little-endian, секции `.data`, `.bss`, `.text`, статические данные и обращение к памяти.

## За 30 секунд

- `x` — адрес метки `x`.
- `[x]` — значение в памяти по адресу `x`.
- `mov eax, x` кладёт в `eax` адрес.
- `mov eax, [x]` читает значение.
- `mov [x], eax` записывает значение.
- `scanf` получает адрес: `push x`.
- `printf` получает значение: `push dword [x]`.

## Минимум после главы

Ты должен уметь:

- объяснить разницу между `x` и `[x]`;
- правильно вызвать `scanf("%d", &x)`;
- правильно вызвать `printf("%d", x)`;
- прочитать и записать `dword` в память;
- объяснить little-endian на числе `0x12345678`.

Можно пока не заучивать:

- `.got`, `.plt`, `.symtab`, `.strtab`;
- детали relocation;
- ELF-секции глубже `.text`, `.data`, `.bss`, `.rodata`.

---

## Главное правило

| NASM | C-похожий смысл | Что происходит |
|---|---|---|
| `x` | `&x` | адрес переменной |
| `[x]` | `x` | значение переменной |
| `mov eax, x` | `eax = &x` | адрес в регистр |
| `mov eax, [x]` | `eax = x` | значение в регистр |
| `mov [x], eax` | `x = eax` | запись в память |

Короткая привычка:

```text
видишь квадратные скобки -> идём в память по адресу
```

---

## Картинка памяти

```asm
section .data
    x dd 123
```

```text
address x
   |
   v
+----------------+
| 123            |
+----------------+
```

Теперь команды:

```asm
mov eax, x      ; eax = address of x
mov eax, [x]    ; eax = 123
mov [x], eax    ; memory[x] = eax
```

---

## Память как массив байтов

Можно думать так:

```cpp
uint8_t memory[...];
```

Адрес — это номер байта.

Если храним `dword`, он занимает 4 соседних байта.

---

## Секции NASM

| Секция | Что лежит |
|---|---|
| `.text` | код |
| `.data` | инициализированные изменяемые данные |
| `.bss` | зарезервированная зануленная память |
| `.rodata` | read-only constants, строки формата |

Пример:

```asm
section .data
    a dd 10
    b dd 20
    fmt db "%d", 10, 0

section .bss
    result resd 1
```

`a` и `b` уже имеют значения. `result` — место под будущий `dword`.

---

## Директивы данных

| Директива | Смысл | Пример |
|---|---|---|
| `db` | define byte | `c db 10` |
| `dw` | define word, 2 байта | `s dw 1000` |
| `dd` | define dword, 4 байта | `x dd 123` |
| `dq` | define qword, 8 байт | `q dq 123456` |
| `resb` | reserve bytes | `buf resb 64` |
| `resw` | reserve words | `arr resw 10` |
| `resd` | reserve dwords | `arr resd 10` |
| `resq` | reserve qwords | `arr resq 10` |

---

## Little-endian

IA-32 хранит многобайтовые числа в little-endian: младший байт лежит по младшему адресу.

```asm
section .data
x dd 0x12345678
```

В памяти:

```text
Address:   x      x+1    x+2    x+3
         +------+------+------+------+
Byte:    |  78  |  56  |  34  |  12  |
         +------+------+------+------+
```

Важно: little-endian — это порядок байтов в памяти, а не порядок цифр в записи числа.

---

## `scanf`: нужен адрес

C:

```c
scanf("%d", &x);
```

NASM:

```asm
push x
push fmtIn
call scanf
add esp, 8
```

Почему `x`?

Потому что `scanf` должен знать, куда записать число.

Плохо:

```asm
push dword [x]
```

`[x]` — старое значение переменной. Это не адрес для записи.

---

## `printf`: нужно значение

C:

```c
printf("%d", x);
```

NASM:

```asm
push dword [x]
push fmtOut
call printf
add esp, 8
```

Почему `[x]`?

Потому что `printf` должен напечатать значение.

Плохо:

```asm
push x
```

Так ты напечатаешь адрес, а не число.

---

## Размер памяти: зачем `dword`

Иногда NASM понимает размер по регистру:

```asm
mov eax, [x]     ; eax 32-bit, читаем dword
```

Но иногда размер не очевиден:

```asm
inc [x]          ; byte? word? dword?
```

Нужно явно:

```asm
inc dword [x]
```

---

## Полный пример

```asm
section .data
    fmtOut db "%d", 10, 0
    x dd 123

section .text
    extern printf
    global main

main:
    push dword [x]
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

Что важно:

| Строка | Смысл |
|---|---|
| `push dword [x]` | положить значение `123` |
| `push fmtOut` | положить адрес строки формата |

---

## Частые ошибки

| Ошибка | Почему плохо | Как правильно |
|---|---|---|
| `push [x]` для `scanf` | передаёшь значение вместо адреса | `push x` |
| `push x` для `printf("%d")` | печатаешь адрес вместо значения | `push dword [x]` |
| `push [fmtOut]` | передаёшь первые 4 байта строки как адрес | `push fmtOut` |
| думать, что `[x]` — адрес | наоборот: это значение по адресу | `x` — адрес, `[x]` — значение |
| забыть little-endian | неправильно читаешь байты в памяти | младший байт лежит первым |
| не указать `dword` там, где размер неясен | NASM не знает размер операции | `inc dword [x]` |

---

## Практика

### A. Trace

Что будет в регистрах?

```asm
section .data
    x dd 123

mov eax, x
mov ecx, [x]
```

Заполни:

| Регистр | Значение |
|---|---|
| `eax` | ? |
| `ecx` | ? |

<details>
<summary>Ответ</summary>

`eax` получает адрес `x`.

`ecx` получает значение `123`.

</details>

### B. Заполни пропуски

```asm
; scanf("%d", &x)
push ___
push fmtIn
call scanf
add esp, ___
```

<details>
<summary>Ответ</summary>

```asm
push x
push fmtIn
call scanf
add esp, 8
```

</details>

### C. Напиши сам

Есть переменная:

```asm
x resd 1
```

Напиши фрагмент, который печатает `x` через `printf("%d\n", x)`.

<details>
<summary>Ответ</summary>

```asm
push dword [x]
push fmtOut
call printf
add esp, 8
```

</details>

### D. Найди баг

```asm
push dword [x]
push fmtIn
call scanf
add esp, 8
```

Что не так?

<details>
<summary>Ответ</summary>

Для `scanf` нужен адрес `x`, а не значение `[x]`.

</details>

---

## Чеклист

Ты готов идти дальше, если можешь без подсказки:

- [ ] объяснить `x` и `[x]`;
- [ ] написать `scanf("%d", &x)` на NASM;
- [ ] написать `printf("%d", x)` на NASM;
- [ ] показать little-endian для `0x12345678`;
- [ ] найти ошибку в `push [x]` перед `scanf`;
- [ ] объяснить, зачем иногда нужен `dword`.
