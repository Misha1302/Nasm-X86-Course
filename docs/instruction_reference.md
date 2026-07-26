# Справочник основных инструкций NASM IA-32

> **ABI-условие для libc.** Перед первым полным фрагментом с `printf`/`scanf` тело функции должно получить `esp % 16 == 0`, например через `push ebp; mov ebp, esp; and esp, -16`. Padding и аргументы вместе занимают кратное 16 число байт; полный вывод находится в [C ABI / CDECL](/c_abi) и [паттерне выравнивания](/patterns/libc_alignment).

> Это справочная карта, а не глава для последовательного заучивания. Открывай её, когда встретил незнакомую команду, и возвращайся к основному дню курса.

Перед первым днём полезно иметь маленькую карту местности. Не надо учить эту таблицу наизусть за один вечер. Смысл другой: когда ты видишь незнакомый фрагмент, быстро находишь команду и вспоминаешь, что она делает.

В NASM почти всегда порядок такой:

```asm
instruction destination, source
```

То есть:

```asm
mov eax, ebx    ; eax = ebx
add eax, 5      ; eax = eax + 5
```

И ещё одно правило, которое спасёт много нервов:

```asm
x       ; адрес метки x
[x]     ; значение в памяти по адресу x
```

### 1. Пересылка данных

| Команда | Пример | Что делает | Как думать на C++ |
|---|---|---|---|
| `mov` | `mov eax, ebx` | копирует значение | `eax = ebx` |
| `mov` | `mov eax, [x]` | читает значение из памяти | `eax = x` |
| `mov` | `mov [x], eax` | записывает значение в память | `x = eax` |
| `movsx` | `movsx eax, byte [x]` | расширяет маленькое signed-значение | `int eax = (signed char)x` |
| `movzx` | `movzx eax, byte [x]` | расширяет маленькое unsigned-значение нулями | `int eax = (unsigned char)x` |
| `lea` | `lea eax, [ebx+4*ecx]` | считает адрес/формулу, не читает память | `eax = ebx + 4*ecx` |
| `push` | `push eax` | кладёт значение на стек | `stack.push(eax)` |
| `pop` | `pop eax` | снимает значение со стека | `eax = stack.pop()` |

Главная ловушка здесь — `lea`. Название похоже на “load”, но память она не читает. Она просто считает выражение в квадратных скобках.

```asm
mov eax, [ebx+4*ecx]   ; прочитать a[i]
lea eax, [ebx+4*ecx]   ; посчитать адрес &a[i]
```

### 2. Целочисленная арифметика

| Команда | Пример | Что делает | Комментарий |
|---|---|---|---|
| `add` | `add eax, ebx` | `eax += ebx` | signed/unsigned результат по битам один и тот же |
| `sub` | `sub eax, 10` | `eax -= 10` | часто используется и для сравнения через `cmp` |
| `inc` | `inc eax` | `eax++` | короткая форма прибавления 1 |
| `dec` | `dec eax` | `eax--` | короткая форма вычитания 1 |
| `neg` | `neg eax` | `eax = -eax` | двоичное дополнение |
| `imul` | `imul eax, ebx` | signed-умножение | удобная форма: `eax *= ebx` |
| `imul` | `imul eax, ebx, 41` | `eax = ebx * 41` | очень полезно для формул |
| `mul` | `mul ebx` | unsigned-умножение `eax * ebx` | полный результат попадает в `edx:eax` |
| `cdq` | `cdq` | расширяет знак `eax` в `edx:eax` | почти всегда перед `idiv` |
| `idiv` | `idiv dword [y]` | signed-деление `edx:eax / y` | частное в `eax`, остаток в `edx` |
| `div` | `div dword [y]` | unsigned-деление `edx:eax / y` | перед ним часто делают `xor edx, edx` |

Запомни ритуал signed-деления:

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

Для unsigned-деления чаще так:

```asm
mov eax, [x]
xor edx, edx
div dword [y]
```

### 3. Битовые операции

| Команда | Пример | Что делает | Где пригодится |
|---|---|---|---|
| `and` | `and eax, mask` | оставляет биты, где в маске 1 | фильтрация битов, masked merge |
| `or` | `or eax, ebx` | ставит биты из обоих операндов | сборка числа из частей |
| `xor` | `xor eax, ebx` | 1 там, где биты различаются | branchless tricks, обнуление |
| `xor` | `xor eax, eax` | быстро делает `eax = 0` | часто в `return 0` |
| `not` | `not eax` | инвертирует все биты | `~x` |
| `shl` / `sal` | `shl eax, 8` | сдвиг влево | `x << 8`, упаковка байтов |
| `shr` | `shr eax, 1` | логический сдвиг вправо | unsigned `x >> 1` |
| `sar` | `sar eax, 31` | арифметический сдвиг вправо | маска знака для `abs` |
| `rol` | `rol eax, cl` | циклический сдвиг влево | задачи на rotate |
| `ror` | `ror eax, cl` | циклический сдвиг вправо | задача “Поворот” |

Мини-пример из домашних:

```asm
; 01-7: pack = a | (b << 8) | (c << 16) | (d << 24)
mov eax, [a]
mov ecx, [b]
shl ecx, 8
or eax, ecx
```

И ещё один:

```asm
; 01-8: result = (a & c) | (b & ~c)
mov eax, [a]
and eax, [c]
mov ecx, [c]
not ecx
and ecx, [b]
or eax, ecx
```

### 4. Сравнения, флаги и переходы

`cmp` и `test` сами по себе никуда не прыгают. Они только выставляют флаги. Прыгают уже команды `j...`.

| Команда | Пример | Что делает | Как думать |
|---|---|---|---|
| `cmp` | `cmp eax, ebx` | выставляет флаги как после `eax - ebx` | сравнение через вычитание |
| `test` | `test eax, eax` | выставляет флаги как после `eax & eax` | проверка на ноль |
| `jmp` | `jmp .loop` | безусловный переход | `goto` |
| `je` / `jz` | `je .equal` | переход, если равно / ноль | `==` |
| `jne` / `jnz` | `jne .not_equal` | переход, если не равно / не ноль | `!=` |
| `jg` | `jg .greater` | signed `>` | для `int` |
| `jge` | `jge .ge` | signed `>=` | для `int` |
| `jl` | `jl .less` | signed `<` | для `int` |
| `jle` | `jle .le` | signed `<=` | для `int` |
| `ja` | `ja .above` | unsigned `>` | для `unsigned` |
| `jae` | `jae .ae` | unsigned `>=` | для `unsigned` |
| `jb` | `jb .below` | unsigned `<` | для `unsigned` |
| `jbe` | `jbe .be` | unsigned `<=` | для `unsigned` |

Пример:

```asm
cmp eax, ebx
jl .less_signed      ; if ((int)eax < (int)ebx)
jb .less_unsigned    ; if ((unsigned)eax < (unsigned)ebx)
```

Один и тот же набор битов может быть `-1` как signed и `4294967295` как unsigned. Поэтому `jl` и `jb` — не одно и то же.

### 5. Функции и стек

| Команда | Пример | Что делает | Как думать |
|---|---|---|---|
| `call` | `call f` | кладёт адрес возврата на стек и прыгает в `f` | вызов функции |
| `ret` | `ret` | достаёт адрес возврата и прыгает туда | выход из функции |
| `leave` | `leave` | аналог `mov esp, ebp; pop ebp` | быстрый эпилог функции |
| `push` | `push arg` | положить аргумент на стек | подготовка вызова |
| `pop` | `pop eax` | снять значение со стека | восстановление/чтение |

Типовой CDECL-вызов:

```asm
push dword [b]
push dword [a]
call sum
add esp, 8
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

Карта фрейма:

```text
[ebp+12]  second argument
[ebp+8]   first argument
[ebp+4]   return address
[ebp]     old ebp
[ebp-4]   first local variable
```

### 6. Минимум x87, чтобы не испугаться вещественных чисел

x87 — отдельная стековая машина для floating point. Её не надо мешать с `eax/ebx`.

| Команда | Пример | Что делает |
|---|---|---|
| `finit` | `finit` | инициализирует x87 |
| `fld` | `fld dword [x]` | кладёт float на x87-стек |
| `fst` | `fst dword [x]` | сохраняет без pop |
| `fstp` | `fstp qword [esp+4]` | сохраняет и делает pop |
| `faddp` | `faddp` | складывает верхние элементы и делает pop |
| `fsubp` | `fsubp` | вычитает и делает pop |
| `fmulp` | `fmulp` | умножает и делает pop |
| `fdivp` | `fdivp` | делит и делает pop |

Главная ловушка:

```asm
; printf("%f", value): выделяем 8 байт под double
sub esp, 12      ; 4 bytes padding + 8-byte double
fstp qword [esp]
push fmt
call printf
add esp, 16
```

Если передать `dword` или не выделить место под восемь байт, `printf` прочитает неверный аргумент.

### 7. Очень короткая шпаргалка “что учить первым”

Сначала уверенно выучи и используй вот этот минимум:

```text
mov, add, sub, imul, cdq, idiv,
and, or, xor, not, shl, shr, sar,
cmp, test, jmp, je, jne, jl, jg, jb, ja,
push, pop, call, ret, lea, movsx, movzx
```

Остальные команды легче учить уже по мере задач.

---
