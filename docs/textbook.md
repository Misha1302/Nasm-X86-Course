# Учебник: NASM x86 / IA-32 без слайдов под рукой

Эта страница — полноценная учебная версия курса. Её задача простая: если рядом нет слайдов, по этому тексту всё равно можно учиться.

Слайды ВШЭ остаются опорой по порядку тем и акцентам, но здесь материал объяснён как самостоятельный конспект: с примерами, схемами, типовыми ошибками и маленькими упражнениями.

## Как читать этот учебник

Не пытайся сразу запомнить все команды. В ассемблере важнее не список мнемоник, а модель:

```text
данные лежат в памяти или регистрах;
инструкция берёт операнды;
результат куда-то записывается;
часть инструкций выставляет флаги;
переходы смотрят на флаги;
функции используют стек.
```

Хороший темп такой:

1. Прочитай раздел.
2. Нарисуй схему от руки.
3. Проговори пример вслух.
4. Реши мини-задачи.
5. Только потом переходи дальше.

> Главное правило: если ты не можешь нарисовать, где лежат данные после инструкции, ты пока не понял тему.

---

## 1. Зачем вообще нужен ассемблер

Ассемблер — это текстовая форма машинных инструкций. Он находится очень близко к тому, что реально исполняет процессор.

Важно: почти никто не пишет большие прикладные программы целиком на asm. Но asm нужен там, где обычный язык слишком далеко от железа.

### Где ассемблер реально встречается

| Где | Зачем |
|---|---|
| ОС, драйверы, загрузчики | нужно управлять железом, регистрами, режимами процессора |
| компиляторы, интерпретаторы, JIT | нужно генерировать или понимать машинный код |
| runtime языков | startup, ABI, атомарные операции, переключение контекстов, низкоуровневая память |
| libc и системные библиотеки | быстрые версии `memcpy`, `strlen`, `memmove`, иногда SIMD |
| кодеки, криптография, математика | горячие участки, где важна скорость |
| reverse engineering и security | нужно читать то, что реально исполняется |
| embedded | мало памяти, особое железо, полный контроль |

Хорошая формулировка:

> Ассемблер используют точечно, когда нужна конкретная инструкция, конкретная архитектура, скорость или полный контроль.

Плохая формулировка:

> Ассемблер быстрее всего, значит всё надо писать на нём.

Современные компиляторы часто генерируют очень хороший код. Ручной asm имеет смысл только когда ты понимаешь, зачем он нужен, и можешь измерить эффект.

### Почему в курсе именно x86 / IA-32

Мы работаем с 32-битной моделью IA-32:

```text
eax, ebx, ecx, edx
esi, edi
esp, ebp
eip, eflags
```

Почему это удобно для обучения:

- регистров немного;
- стековые аргументы хорошо видны;
- `ebp`, `[ebp+8]`, `[ebp-4]` отлично показывают функции;
- задачи курса используют `nasm-x86`;
- проще увидеть связь C/C++ и машинного кода.

x64 существует, но пока его не мешаем сюда. Там другие регистры и другое соглашение вызова.

---

## 2. Путь от C++ до выполняющейся программы

Когда ты пишешь C++, процессор не видит твой исходник напрямую.

```text
C++ source
   |
   | compiler
   v
Assembly source
   |
   | assembler
   v
Object file (.o)
   |
   | linker
   v
Executable
   |
   | OS loader
   v
Process in memory
   |
   | CPU executes instructions
   v
Result
```

Для NASM-файла путь короче:

```text
main.asm
   |
   | nasm -f elf32
   v
main.o
   |
   | gcc -m32 -no-pie
   v
main
   |
   | ./main
   v
output
```

### Команды Linux

```bash
nasm -f elf32 main.asm -o main.o
gcc -m32 -no-pie main.o -o main
./main
```

Если нужны отладочные символы:

```bash
nasm -f elf32 -g -F dwarf main.asm -o main.o
gcc -m32 -g -no-pie main.o -o main
```

Почему в командах есть `-no-pie`?

Наши первые NASM-примеры используют простые абсолютные адреса меток: `x`, `fmtOut`, `.table`. На современных Linux `gcc` может по умолчанию собирать PIE-executable, а это требует другой модели адресации. Поэтому для учебного IA-32 кода используем `-no-pie`, а PIE/GOT/PLT разбираем отдельно позже.

Посмотреть, что получилось:

```bash
objdump -d -M intel main
objdump -h main
objdump -s -j .data main
```

### Частая ошибка

`.o` — это ещё не программа. Это object file: кусок машинного кода и данных, который ещё надо слинковать.

---

## 3. Модель процессора

Процессор можно представить грубо так:

```text
+---------------- CPU ----------------+
| registers: eax ebx ecx edx ...      |
| eip: адрес следующей инструкции     |
| eflags: признаки результата         |
| ALU: арифметика и логика            |
+------------------|------------------+
                   v
+---------------- RAM ----------------+
| code | data | heap | stack | ...    |
+--------------------------------------+
```

Процессор делает очень простые шаги:

1. взять инструкцию по адресу `eip`;
2. понять opcode и операнды;
3. выполнить операцию;
4. записать результат;
5. перейти к следующей инструкции.

### Операнды

Операнд — это то, с чем работает инструкция.

| Вид операнда | Пример | Как думать |
|---|---|---|
| register | `eax` | быстрая ячейка внутри CPU |
| memory | `[ebp-4]` | значение в памяти по адресу |
| immediate | `123` | константа прямо в инструкции |

Примеры:

```asm
mov eax, ecx              ; register <- register
mov ecx, dword [0x2019]   ; register <- memory
mov dword [ebp-4], ebx    ; memory <- register
add eax, 0xff             ; register += immediate
```

`add eax, ebx` означает не просто `eax + ebx`, а именно:

```cpp
eax = eax + ebx;
```

То есть первый операнд обычно и источник, и приёмник результата.

---

## 4. Регистры IA-32

Регистры — это маленькие быстрые ячейки внутри CPU.

| Регистр | Частая роль в курсе |
|---|---|
| `eax` | аккумулятор, результат функции |
| `ebx` | общий регистр, в CDECL обычно callee-saved |
| `ecx` | счётчик, сдвиги через `cl` |
| `edx` | старшая часть `edx:eax`, остаток после деления |
| `esi` | индекс/указатель-источник |
| `edi` | индекс/указатель-приёмник |
| `esp` | stack pointer, вершина стека |
| `ebp` | frame pointer, база фрейма функции |
| `eip` | адрес следующей инструкции |
| `eflags` | флаги результата |

### Вложенность `eax`, `ax`, `ah`, `al`

Это нужно прям нарисовать.

```text
31                              16 15       8 7        0
+--------------------------------+----------+----------+
|          high 16 bits          |    AH    |    AL    |
+--------------------------------+----------+----------+
                                  \__________ _________/
                                             |
                                             AX

EAX = 32 bits
AX  = low 16 bits of EAX
AH  = high byte of AX
AL  = low byte of AX
```

Пример:

```text
eax = 0x12345678
ax  =     0x5678
ah  =       0x56
al  =       0x78
```

Если сделать:

```asm
mov al, 0
```

то `eax` станет:

```text
0x12345600
```

Потому что `al` — это младший байт `eax`, а не отдельная переменная.

### Размеры данных

| NASM | Биты | Байты | Похоже на C/C++ |
|---|---:|---:|---|
| `byte` | 8 | 1 | `char`, `uint8_t` |
| `word` | 16 | 2 | `short` |
| `dword` | 32 | 4 | `int`, pointer в IA-32 |
| `qword` | 64 | 8 | `long long`, `double` |

---

## 5. Память, секции и `x` против `[x]`

Память — это большой массив байтов. Адрес — номер байта в этом массиве.

```text
memory[address] = byte
```

### Секции NASM

```asm
section .text   ; код
section .data   ; инициализированные данные
section .bss    ; зарезервированная память
section .rodata ; read-only данные, строки формата
```

Пример:

```asm
section .data
    x dd 123
    fmt db "%d", 10, 0

section .bss
    buffer resd 10
```

| Директива | Что делает |
|---|---|
| `db` | define byte |
| `dw` | define word |
| `dd` | define dword |
| `dq` | define qword |
| `resb` | reserve bytes |
| `resw` | reserve words |
| `resd` | reserve dwords |
| `resq` | reserve qwords |

### Little-endian

В IA-32 младший байт лежит по меньшему адресу.

```asm
x dd 0x12345678
```

В памяти:

```text
Address:   x      x+1    x+2    x+3
         +------+------+------+------+
Byte:    |  78  |  56  |  34  |  12  |
         +------+------+------+------+
```

### Главное правило `x` и `[x]`

```asm
mov eax, x      ; eax = address of x
mov eax, [x]    ; eax = value stored at x
mov [x], eax    ; memory[x] = eax
```

В C++-аналогии:

| NASM | C++-смысл |
|---|---|
| `x` | `&x` |
| `[x]` | `*(&x)`, значение `x` |
| `mov eax, x` | положить адрес в `eax` |
| `mov eax, [x]` | прочитать значение |
| `mov [x], eax` | записать значение |

Частая ошибка:

```asm
push [x] ; плохо для scanf: это значение
push x   ; хорошо для scanf: это адрес
```

---

## 6. Первая программа с `scanf` и `printf`

Минимальный шаблон:

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

Пока можно думать так:

```text
scanf("%d", &x)  -> нужен адрес x
printf("%d", x) -> нужно значение x
```

### Почему `add esp, 8`

В 32-битном CDECL аргументы кладутся на стек. Один аргумент занимает 4 байта. Мы положили два аргумента:

```asm
push x      ; 4 bytes
push fmtIn  ; 4 bytes
```

После вызова надо убрать 8 байт:

```asm
add esp, 8
```

Полную теорию CDECL разберём позже, но этот шаблон уже нужен для задач.

### Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| `push [x]` перед `scanf` | `scanf` нужен адрес, а не старое значение |
| `push [fmtIn]` | строка формата передаётся адресом |
| забыть `add esp, 8` | стек разбалансируется |
| не указать `dword` | NASM иногда не может вывести размер |

---

## 7. Арифметика и вопрос “почему нет `iadd`”

Базовые команды:

```asm
mov eax, [a]
add eax, [b]
sub eax, 10
inc eax
dec eax
neg eax
```

### Почему `add`, а не `iadd`

В x86 есть `mul/imul` и `div/idiv`, но нет `add/iadd`.

Причина: сложение и вычитание дают одинаковый битовый результат для signed и unsigned. Разница в том, как мы потом читаем результат и флаги.

8-битный пример:

```text
  11111111
+ 00000001
-----------
1 00000000
  ^^^^^^^^ stored result
```

Это можно прочитать как:

```text
unsigned: 255 + 1 = 0 mod 256
signed:   -1 + 1 = 0
```

Биты результата одинаковые. Но флаги интерпретируются по-разному:

| Флаг | Что показывает |
|---|---|
| `CF` | перенос/заём для unsigned |
| `OF` | переполнение для signed |
| `ZF` | результат равен нулю |
| `SF` | знаковый бит результата |

Поэтому отдельная команда `iadd` не нужна.

### Упражнение

Посчитай в 8 битах:

```text
127 + 1
255 + 1
-1 + 1
-128 - 1
```

<details>
<summary>Ответы</summary>

`127 + 1 = 128`, но для signed 8-bit это переполнение: `01111111 + 00000001 = 10000000`, то есть `-128`.

`255 + 1 = 0 mod 256`, будет carry.

`-1 + 1 = 0`.

`-128 - 1` в 8 битах даст `127` с signed overflow.

</details>

---

## 8. `movsx`, `movzx`, `cbw`, `cwd`, `cdq`

Один и тот же байт может означать разные числа.

```text
0xFF = 11111111
```

Как `unsigned char` это `255`.
Как `signed char` это `-1`.

### Zero extension

```asm
movzx eax, byte [x]
```

Если `x = 0xFF`, то:

```text
eax = 0x000000FF
```

### Sign extension

```asm
movsx eax, byte [x]
```

Если `x = 0xFF`, то:

```text
eax = 0xFFFFFFFF
```

Потому что старший бит байта равен 1, значит число отрицательное, и знак размножается.

### Команды расширения

| Команда | Что делает |
|---|---|
| `movzx` | расширяет нулями |
| `movsx` | расширяет знаковым битом |
| `cbw` | `AL -> AX` sign extension |
| `cwd` | `AX -> DX:AX` sign extension |
| `cdq` | `EAX -> EDX:EAX` sign extension |

`cdq` особенно важна перед `idiv`.

---

## 9. Умножение и деление

Умножение и деление в x86 выглядят страннее, чем в C++.

### Умножение

Часто удобна такая форма:

```asm
imul eax, ebx       ; eax *= ebx
imul eax, ebx, 41   ; eax = ebx * 41
```

Есть и историческая форма:

```asm
mul ebx   ; unsigned: edx:eax = eax * ebx
imul ebx  ; signed:   edx:eax = eax * ebx
```

Почему `edx:eax`? Потому что результат 32x32 может занимать 64 бита.

### Деление

Для 32-битного деления делимое лежит в паре `edx:eax`.

```text
+----------------+----------------+
|      edx       |      eax       |
+----------------+----------------+
   high              low
```

Команды:

| Operation | Unsigned | Signed |
|---|---|---|
| multiply | `mul` | `imul` |
| divide | `div` | `idiv` |
| prepare dividend | `xor edx, edx` | `cdq` |
| quotient | `eax` | `eax` |
| remainder | `edx` | `edx` |

Signed division:

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

Unsigned division:

```asm
mov eax, [x]
xor edx, edx
div dword [y]
```

### Типовые ошибки

```asm
idiv eax, ecx ; так нельзя
```

У `idiv` один явный операнд — делитель. Делимое уже в `edx:eax`.

---

## 10. Биты, сдвиги, маски и домашки 01-7…01-10

Это центральный раздел для первых домашних задач.

### Битовые команды

| Команда | Что делает |
|---|---|
| `and` | оставляет 1 только там, где в обоих операндах 1 |
| `or` | ставит 1, если хотя бы где-то 1 |
| `xor` | ставит 1, если биты различаются |
| `not` | инвертирует все биты |
| `shl` / `sal` | сдвиг влево |
| `shr` | логический сдвиг вправо, сверху нули |
| `sar` | арифметический сдвиг вправо, копирует знак |
| `rol` / `ror` | циклические сдвиги |

### 01-7: Упаковка вектора

Нужно из четырёх байтов собрать одно 32-битное число:

```text
31..24      23..16      15..8       7..0
+-----------+-----------+-----------+-----------+
|     d     |     c     |     b     |     a     |
+-----------+-----------+-----------+-----------+
```

Формула:

```cpp
x = a | (b << 8) | (c << 16) | (d << 24);
```

NASM-идея:

```asm
mov eax, [a]
mov ecx, [b]
shl ecx, 8
or eax, ecx

mov ecx, [c]
shl ecx, 16
or eax, ecx

mov ecx, [d]
shl ecx, 24
or eax, ecx
```

Проверка:

```text
a=1, b=2, c=3, d=4
x = 0x04030201 = 67305985
```

### 01-8: Masked merge

Нужно выбрать каждый бит из `a` или `b` по маске `c`:

```cpp
d[i] = c[i] ? a[i] : b[i];
```

Формула:

```cpp
d = (a & c) | (b & ~c);
```

Почему работает:

```text
a & c   -> оставляет биты a там, где c=1
b & ~c  -> оставляет биты b там, где c=0
or      -> склеивает две части
```

NASM:

```asm
mov eax, [a]
and eax, [c]

mov ecx, [c]
not ecx
and ecx, [b]

or eax, ecx
```

### 01-9: Модуль числа без переходов

Нельзя использовать условные переходы и `cmov`.

Branchless formula:

```cpp
mask = x >> 31;
answer = (x ^ mask) - mask;
```

NASM:

```asm
mov eax, [x]
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
```

Почему работает:

- если `x >= 0`, `mask = 0`, ответ `x`;
- если `x < 0`, `mask = -1 = 0xFFFFFFFF`, ответ `~x + 1 = -x`.

Важная ошибка: нужен `sar`, не `shr`.

### 01-10: Год на Пандоре

Месяцы чередуются:

```text
1: 41 days
2: 42 days
3: 41 days
4: 42 days
...
```

Даны `month` и `day`, оба с 1. Нужно найти номер дня в году.

Количество предыдущих месяцев:

```cpp
before = month - 1;
```

Каждый предыдущий месяц даёт минимум 41 день. Каждый второй предыдущий месяц даёт ещё +1.

Формула:

```cpp
answer = before * 41 + before / 2 + day;
```

NASM:

```asm
mov eax, [month]
sub eax, 1        ; before
mov ecx, eax
imul eax, 41
shr ecx, 1        ; before / 2
add eax, ecx
add eax, [day]
```

---

## 11. EFLAGS: лампочки после инструкции

Флаги — это признаки результата последней операции.

```text
+----+----+----+----+----+----+
| OF | SF | ZF | AF | PF | CF |
+----+----+----+----+----+----+
  |    |    |    |    |    +-- unsigned carry/borrow
  |    |    |    |    +------- parity
  |    |    |    +------------ auxiliary carry
  |    |    +----------------- zero result
  |    +---------------------- sign bit
  +--------------------------- signed overflow
```

Главные флаги:

| Flag | Meaning |
|---|---|
| `ZF` | result is zero |
| `SF` | sign bit of result |
| `CF` | unsigned carry/borrow |
| `OF` | signed overflow |
| `PF` | parity of low byte |
| `AF` | auxiliary carry, исторически важен для BCD |

Примеры:

```asm
xor eax, eax    ; eax = 0, ZF=1
add eax, ebx    ; обновляет арифметические флаги
and eax, ebx    ; обновляет ZF/SF/PF, сбрасывает CF/OF
```

Частая ошибка: между `cmp` и `jcc` поставить инструкцию, которая меняет флаги.

---

## 12. `cmp`, `test`, условные переходы

`cmp` называется compare, но внутри это вычитание без сохранения результата.

```asm
cmp eax, ebx
```

Мысленно:

```text
temp = eax - ebx
temp is not stored
flags are updated
```

Если `temp == 0`, то `ZF=1`.

`test` — это `and` без сохранения результата.

```asm
test eax, eax
je .zero
```

Так проверяют `eax == 0`.

### Signed и unsigned переходы

| Jump | Meaning |
|---|---|
| `je` / `jz` | equal / zero |
| `jne` / `jnz` | not equal / not zero |
| `jg` | signed `>` |
| `jge` | signed `>=` |
| `jl` | signed `<` |
| `jle` | signed `<=` |
| `ja` | unsigned `>` |
| `jae` | unsigned `>=` |
| `jb` | unsigned `<` |
| `jbe` | unsigned `<=` |

Пример:

```text
eax = 0xFFFFFFFF
ebx = 1
```

Как signed:

```text
-1 < 1
```

Как unsigned:

```text
4294967295 > 1
```

Поэтому для тех же битов `jl` и `ja` могут говорить разные вещи.

---

## 13. `if`, циклы и GOTO-форма

В asm нет `if`, `while`, `for`. Есть метки и переходы.

C++:

```cpp
if (x > y) {
    result = x - y;
} else {
    result = y - x;
}
```

ASM-shape:

```asm
cmp x, y
jle .else

.then:
    ; result = x - y
    jmp .end

.else:
    ; result = y - x

.end:
```

Цикл `while`:

```cpp
while (x != 0) {
    x >>= 1;
}
```

ASM-shape:

```asm
.loop:
    test eax, eax
    je .end
    shr eax, 1
    jmp .loop
.end:
```

Popcount:

```asm
xor ecx, ecx        ; result = 0
.loop:
    test edx, edx
    je .end
    mov eax, edx
    and eax, 1
    add ecx, eax
    shr edx, 1
    jmp .loop
.end:
```

Типовая ошибка: забыть `jmp .end` после then-ветки в `if/else`.

---

## 14. `switch` и jump table

`switch` может стать цепочкой сравнений, а может стать таблицей переходов.

```asm
cmp eax, 5
ja .default
jmp [.table + 4*eax]

.table:
dd .case0
dd .case1
dd .case2
dd .case3
dd .case4
dd .case5
```

Это значит:

```text
если eax > 5 unsigned -> default
иначе взять адрес из table[eax] и прыгнуть туда
```

### Обратная задача

```asm
add eax, 2
cmp eax, 6
ja .L2
jmp [.L8 + 4*eax]

section .rodata
.L8 dd .L3, .L2, .L4, .L5, .L6, .L6, .L7
```

Как читать:

1. `add eax, 2` сдвигает диапазон. Если исходное `x`, то индекс `x+2`.
2. `cmp eax, 6` значит допустимые индексы `0..6`.
3. Таблица имеет 7 элементов.
4. Повтор `.L6, .L6` значит два case ведут в одну ветку.
5. `.L2` может быть default или одной из веток, надо смотреть дальше.

---

## 15. Адресация, `lea`, массивы

Главная форма памяти:

```asm
[base + index * scale + displacement]
```

Пример:

```asm
[eax + ecx*4 + 8]
```

```text
base = eax
index = ecx
scale = 4
displacement = 8
```

### `mov` против `lea`

```asm
mov eax, [edx + 4*ecx]   ; eax = a[i]
lea eax, [edx + 4*ecx]   ; eax = &a[i]
```

`lea` не читает память. Она считает адрес или арифметическое выражение.

### Массивы

```cpp
int a[5];
```

В памяти:

```text
a+0    a+4    a+8    a+12   a+16
+------+------+------+------+------+
| a[0] | a[1] | a[2] | a[3] | a[4] |
+------+------+------+------+------+
```

Адрес:

```cpp
&a[i] = base + 4*i
```

2D row-major:

```cpp
int a[R][C];
&a[i][j] = base + 4 * (i*C + j)
```

---

## 16. Стек, `push`, `pop`, `call`, `ret`

Стек растёт вниз, к меньшим адресам.

```text
Before push eax:
0x100C | old data |
0x1008 | old data | <- esp

After push eax:
0x100C | old data |
0x1008 | old data |
0x1004 |   eax    | <- esp
```

Команды:

| Instruction | Effect |
|---|---|
| `push eax` | `esp -= 4; [esp] = eax` |
| `pop eax` | `eax = [esp]; esp += 4` |
| `call f` | push return address, jump to `f` |
| `ret` | pop return address into `eip` |

Пример:

```asm
push 10
push 20
pop eax     ; eax = 20
pop ebx     ; ebx = 10
```

`call` — это прыжок с запиской, куда вернуться:

```text
call f:
1. push address_after_call
2. jump to f

ret:
1. pop return_address
2. jump to return_address
```

---

## 17. Фрейм функции и CDECL

После пролога:

```asm
push ebp
mov ebp, esp
sub esp, N
```

фрейм выглядит так:

```text
higher addresses
+------------------+
| argument 2       | [ebp+12]
+------------------+
| argument 1       | [ebp+8]
+------------------+
| return address   | [ebp+4]
+------------------+
| old ebp          | [ebp]
+------------------+
| local variable 1 | [ebp-4]
+------------------+
| local variable 2 | [ebp-8]
+------------------+
lower addresses
```

Типовая функция:

```asm
sum:
    push ebp
    mov ebp, esp

    mov eax, [ebp+8]
    add eax, [ebp+12]

    pop ebp
    ret
```

Вызов:

```asm
push dword [b]
push dword [a]
call sum
add esp, 8
```

CDECL:

| Правило | Смысл |
|---|---|
| arguments right-to-left | сначала push последнего аргумента |
| caller cleans stack | после `call` вызывающий делает `add esp, ...` |
| return in `eax` | обычный int-результат в `eax` |
| `eax/ecx/edx` caller-saved | функция может их испортить |
| `ebx/esi/edi` callee-saved | функция должна восстановить |

Частая ошибка: думать, что первый аргумент — `[ebp+4]`. Нет, `[ebp+4]` — return address.

---

## 18. Reverse engineering: читаем asm как следы C

Цель не восстановить исходник идеально, а понять смысл.

Шпаргалка:

| ASM pattern | Possible C meaning |
|---|---|
| `[ebp+8]` | first argument |
| `[ebp+12]` | second argument |
| `[ebp-4]` | local variable |
| `movsx eax, byte [...]` | signed char to int |
| `movzx eax, word [...]` | unsigned short to int |
| `lea eax, [base+4*i]` | address of `array[i]` |
| `mov eax, [base+4*i]` | read `array[i]` |
| `mov [eax], edx` | write through pointer |
| final `eax` | return value |

Пример:

```asm
movsx edx, byte [ebp+12]
mov eax, [ebp+16]
mov [eax], edx
movsx eax, word [ebp+8]
mov edx, [ebp+20]
sub edx, eax
mov eax, edx
```

Возможный C-смысл:

```cpp
int f(short c, signed char d, int* p, int x)
{
    *p = d;
    return x - c;
}
```

Почему:

- `[ebp+8]` используется как `word` и `movsx` → signed short;
- `[ebp+12]` используется как `byte` и `movsx` → signed char;
- `[ebp+16]` загружается в `eax`, потом `[eax]` записывается → pointer;
- финальный результат кладётся в `eax`.

---

## 19. Структуры, объединения, выравнивание

Структура — непрерывный блок памяти. Имена полей в памяти не лежат. Есть только offset.

```cpp
struct rec {
    int i;
    int j;
    int a[3];
    rec* p;
};
```

IA-32 layout:

```text
offset:  0      4      8      12     16     20
       +------+------+------+------+------+------+
field: |  i   |  j   | a[0] | a[1] | a[2] |  p   |
       +------+------+------+------+------+------+
```

Если `edx = r`:

```asm
mov eax, [edx]                 ; r->i
mov eax, [edx+4]               ; r->j
mov eax, [edx + 4*ecx + 8]     ; r->a[ecx]
mov edx, [edx + 20]            ; r = r->p
```

### Padding

```cpp
struct S1 {
    char c;
    int x;
    char d;
};
```

Возможный layout:

```text
+---+---+---+---+---+---+---+---+---+---+---+---+
| c | p | p | p |       x       | d | p | p | p |
+---+---+---+---+---+---+---+---+---+---+---+---+
```

Поля выравниваются, поэтому `sizeof` не всегда равен простой сумме размеров.

---

## 20. Что происходит до `main` и после него

`main` — не первая инструкция процесса.

```text
OS loader
   |
   v
_start
   |
   v
__libc_start_main(...)
   |
   v
constructors / init
   |
   v
main(argc, argv, envp)
   |
   v
destructors / fini
   |
   v
exit
```

Стадии:

| Stage | Artifact/action |
|---|---|
| preprocessing | expanded source |
| compilation | assembly |
| assembling | object `.o` |
| linking | executable |
| loading | process in memory |
| startup | `_start`, libc |
| user code | `main` |

Полезные команды:

```bash
objdump -h main
objdump -d -M intel main
objdump -s -j .init_array main
objdump -s -j .fini_array main
```

---

## 21. Ошибки памяти и защиты

В C/C++ выход за границы массива — это не “исключение”, а обращение к соседней памяти.

```cpp
int a[3];
a[10] = 123;
```

На стеке рядом могут быть служебные данные:

```text
higher addresses
+------------------+
| return address   |
+------------------+
| saved ebp        |
+------------------+
| canary           |
+------------------+
| local buffer     |
+------------------+
lower addresses
```

Защиты:

| Defense | Idea |
|---|---|
| Stack canary | detect overwritten frame |
| ASLR | randomize addresses |
| DEP/NX | data pages are not executable |
| FORTIFY_SOURCE | runtime checks for some libc calls |
| CFI/CET | restrict valid control-flow transfers |

Важно: этот раздел нужен, чтобы понимать баги и защиты, а не чтобы эксплуатировать системы.

---

## 22. Вещественные числа

Целые числа представляются точно в фиксированном количестве битов. Вещественные — нет.

Например:

```text
5.75 decimal = 101.11 binary
5 = 101
0.75 = 1/2 + 1/4 = .11
```

Но:

```text
1/10 = 0.0001100110011... binary
```

поэтому `0.1` обычно не представляется точно.

### Float layout

```text
float, 32 bits:

31     30          23 22                    0
+--------+------------+----------------------+
| sign   | exponent   | fraction             |
+--------+------------+----------------------+
```

Special values:

| exponent | fraction | Meaning |
|---|---|---|
| all zero | zero | +0 / -0 |
| all zero | non-zero | denormalized |
| normal | any | normalized |
| all ones | zero | infinity |
| all ones | non-zero | NaN |

---

## 23. x87 FPU

x87 — отдельная стековая машина для floating point.

```text
x87 register stack:

+-----------+
|   st(7)   |
+-----------+
|   ...     |
+-----------+
|   st(1)   |  y
+-----------+
|   st(0)   |  x  <- top
+-----------+
```

Команды:

| Instruction | Meaning |
|---|---|
| `finit` | initialize x87 |
| `fld dword [x]` | push float value |
| `fst dword [x]` | store without pop |
| `fstp qword [x]` | store and pop |
| `faddp` | add and pop |
| `fsubp` | subtract and pop |
| `fmulp` | multiply and pop |
| `fdivp` | divide and pop |

Пример:

```asm
fld dword [x]
fld dword [y]
faddp
fstp qword [esp + 4] ; for printf("%f")
```

Главная ловушка:

```text
printf("%f") expects double, so pass qword, not dword.
```

---

## 24. C++ object model

C++-объект можно думать как структуру плюс служебные поля.

Если есть virtual methods, обычно появляется `vptr`:

```text
Object:

+------------------+
| vptr             | ---> +---------------------+
+------------------+      | virtual method #0   |
| field1           |      +---------------------+
+------------------+      | virtual method #1   |
| field2           |      +---------------------+
+------------------+
```

Идеи:

| C++ feature | Low-level idea |
|---|---|
| field | fixed offset |
| method | function + hidden `this` |
| virtual method | function pointer from VMT |
| inheritance | extended layout |
| RTTI | runtime type information |

Упрощённая форма virtual call:

```asm
mov eax, [obj]        ; load vptr, simplified
call dword [eax]      ; indirect call
```

Реальный код зависит от ABI и компилятора, но идея такая: адрес функции берётся не напрямую из метки, а через таблицу.

---

## 25. Финальная проверка

Ты готов, если можешь без подсказок:

| Skill | Ready if you can... |
|---|---|
| Bits | solve 01-7, 01-8, 01-9, 01-10 |
| Flags | explain `cmp`, `test`, signed/unsigned jumps |
| Stack | draw `push`, `pop`, `call`, `ret`, frame |
| ABI | write and call simple CDECL function |
| Addressing | explain `[base+index*scale+offset]` |
| Reverse | restore simple C from asm |
| Structures | calculate offsets and padding |
| x87 | explain stack model and `%f` double issue |

### Mini mock exam

1. Напиши `abs(x)` без условных переходов.
2. Собери 4 байта в dword.
3. Объясни `cmp eax, ebx` + `jl` и `jb`.
4. Нарисуй фрейм функции с двумя аргументами и двумя локальными переменными.
5. Объясни разницу `mov eax, [edx+4*ecx]` и `lea eax, [edx+4*ecx]`.
6. Восстанови C-смысл:

```asm
mov eax, [ebp+8]
add eax, [ebp+12]
ret
```

Ответ:

```cpp
return arg1 + arg2;
```

### Последняя мысль

Ассемблер становится понятным не тогда, когда ты выучил 100 команд. Он становится понятным, когда ты видишь движение данных:

```text
память -> регистр -> операция -> флаги/память/стек
```

Именно это и проверяет нормальная подготовка к экзамену.
