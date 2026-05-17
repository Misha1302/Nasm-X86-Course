# Популярные полезные инструкции NASM x86

## Зачем эта страница

В x86 есть очень много инструкций, но для учебных задач по NASM x86 нужен небольшой рабочий набор. Его лучше знать не как словарь, а как инструменты для типовых действий: взять данные, посчитать, проверить условие, перейти, вызвать функцию.

Боевой минимум:

```text
mov, lea, movsx, movzx
add, sub, inc, dec, neg, imul, cdq, div, idiv
and, or, xor, not, shl, shr, sar
cmp, test, jmp, je, jne, jl, jle, jg, jge, jb, jbe, ja, jae
push, pop, call, ret, leave
```

---

## 1. Движение данных

| Инструкция | Что делает | Пример |
|---|---|---|
| `mov` | копирует значение | `mov eax, [x]` |
| `lea` | считает адрес, не читает память | `lea eax, [edx+4*ecx]` |
| `movsx` | signed-расширение | `movsx eax, byte [x]` |
| `movzx` | unsigned-расширение | `movzx eax, byte [x]` |

### `mov`

```asm
mov eax, ebx      ; eax = ebx
mov eax, [x]      ; eax = value at address x
mov [x], eax      ; value at address x = eax
mov eax, 123      ; eax = 123
```

`mov` копирует, а не переносит. Источник не очищается.

### `lea`

```asm
lea eax, [edx + 4*ecx]   ; eax = edx + 4*ecx
mov eax, [edx + 4*ecx]   ; eax = memory[edx + 4*ecx]
```

Главная разница:

```text
mov с [addr] читает память;
lea только считает адрес/выражение.
```

### `movsx` и `movzx`

```asm
movsx eax, byte [x]   ; signed char -> int
movzx eax, byte [x]   ; unsigned char -> int
```

Для байта `0xFF`:

```text
movsx -> 0xFFFFFFFF = -1
movzx -> 0x000000FF = 255
```

---

## 2. Арифметика

| Инструкция | Что делает | Пример |
|---|---|---|
| `add` | сложение | `add eax, ebx` |
| `sub` | вычитание | `sub eax, 10` |
| `inc` | +1 | `inc eax` |
| `dec` | -1 | `dec eax` |
| `neg` | сменить знак | `neg eax` |
| `imul` | signed-умножение | `imul eax, 41` |

### `add`, `sub`

```asm
add eax, ebx      ; eax = eax + ebx
sub eax, 10       ; eax = eax - 10
```

Первый операнд меняется.

### `inc`, `dec`

```asm
inc eax           ; eax++
dec eax           ; eax--
```

Тонкость: `inc/dec` не меняют `CF`. Для простых задач это редко важно, но при строгом анализе флагов лучше помнить.

### `neg`

```asm
neg eax           ; eax = -eax
```

На уровне битов:

```text
-x = ~x + 1
```

### `imul`

```asm
imul eax, ebx        ; eax = eax * ebx
imul eax, 41         ; eax = eax * 41
imul eax, ebx, 41    ; eax = ebx * 41
```

Для учебных задач обычно хватает этих форм.

---

## 3. Деление

| Инструкция | Что делает | Когда нужна |
|---|---|---|
| `cdq` | расширяет знак `eax` в `edx:eax` | перед `idiv` |
| `idiv` | signed-деление | для `int` |
| `div` | unsigned-деление | для `unsigned` |

Signed-шаблон:

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

Unsigned-шаблон:

```asm
mov eax, [x]
xor edx, edx
div dword [y]
; eax = x / y
; edx = x % y
```

Главное:

```text
делимое = edx:eax
делитель = явный операнд
частное = eax
остаток = edx
```

---

## 4. Битовые операции

| Инструкция | Что делает | Пример |
|---|---|---|
| `and` | оставить только общие единицы | `and eax, 255` |
| `or` | склеить биты | `or eax, ebx` |
| `xor` | 1 там, где биты разные | `xor eax, eax` |
| `not` | инвертировать все биты | `not eax` |

### Частые идиомы

```asm
xor eax, eax      ; eax = 0
and eax, 255      ; оставить младший байт
not ebx           ; ebx = ~ebx
or eax, ebx       ; склеить непересекающиеся части
```

---

## 5. Сдвиги

| Инструкция | Что делает | Пример |
|---|---|---|
| `shl` | сдвиг влево | `shl ebx, 8` |
| `shr` | логический сдвиг вправо | `shr ebx, 1` |
| `sar` | арифметический сдвиг вправо | `sar edx, 31` |

```asm
shl eax, 8        ; eax <<= 8
shr eax, 1        ; unsigned eax /= 2
sar eax, 31       ; получить 0 или -1 по знаку
```

`shr` добавляет слева нули. `sar` копирует знаковый бит. Для отрицательных signed-чисел это принципиальная разница.

---

## 6. Сравнение и проверка

### `cmp`

```asm
cmp eax, ebx
```

Это как:

```text
eax - ebx
```

но результат не сохраняется, обновляются только флаги.

### `test`

```asm
test eax, eax
```

Это как:

```text
eax & eax
```

без сохранения результата. Используется для проверки на ноль.

Идиомы:

```asm
test eax, eax
je .zero

test eax, 1
jne .odd
```

---

## 7. Переходы

| Переход | Смысл |
|---|---|
| `jmp` | безусловный переход |
| `je` / `jz` | равно / ноль |
| `jne` / `jnz` | не равно / не ноль |
| `jl` | signed `<` |
| `jle` | signed `<=` |
| `jg` | signed `>` |
| `jge` | signed `>=` |
| `jb` | unsigned `<` |
| `jbe` | unsigned `<=` |
| `ja` | unsigned `>` |
| `jae` | unsigned `>=` |

Главная ловушка:

```text
jl != jb
jg != ja
```

Для `int` обычно нужны `jl/jle/jg/jge`. Для `unsigned`, размеров и индексов — `jb/jbe/ja/jae`.

---

## 8. Стек и функции

| Инструкция | Что делает |
|---|---|
| `push` | положить значение на стек |
| `pop` | снять значение со стека |
| `call` | вызвать функцию |
| `ret` | вернуться из функции |
| `leave` | короткий эпилог функции |

```asm
push eax          ; esp -= 4; [esp] = eax
pop eax           ; eax = [esp]; esp += 4
call f            ; push return_address; jump f
ret               ; pop return_address; jump back
```

`leave` примерно равно:

```asm
mov esp, ebp
pop ebp
```

---

## 9. x87 для floating point

Для первых integer-задач не нужно, но в курсе полезно знать:

| Инструкция | Что делает |
|---|---|
| `finit` | инициализировать x87 |
| `fld` | положить float/double на x87-стек |
| `fst` | сохранить без pop |
| `fstp` | сохранить и pop |
| `faddp` | сложить и pop |
| `fsubp` | вычесть и pop |
| `fmulp` | умножить и pop |
| `fdivp` | разделить и pop |

Пример:

```asm
fld dword [a]
fld dword [b]
faddp
fstp qword [esp]
```

Для `printf("%f")` нужен `qword`, потому что `%f` ожидает `double`.

---

## 10. Самые частые ошибки

| Ошибка | Почему плохо |
|---|---|
| `mov eax, x` вместо `mov eax, [x]` | получил адрес, а не значение |
| `push [x]` для `scanf` | `scanf` нужен адрес `x` |
| забыть `add esp, 8` после `printf` | стек несбалансирован |
| забыть `cdq` перед `idiv` | мусор в `edx:eax` |
| `shr` вместо `sar` для знака | неправильная маска знака |
| перепутать `jl` и `jb` | signed/unsigned перепутаны |
| поставить `add` между `cmp` и `je` | флаги перезаписаны |
| думать, что `lea` читает память | `lea` только считает адрес |

---

## 11. Боевой минимум перед задачами

```text
mov, lea, movsx, movzx
add, sub, imul, cdq, idiv, div
and, or, xor, not, shl, shr, sar
cmp, test
jmp, je, jne, jl, jle, jg, jge, jb, jbe, ja, jae
push, pop, call, ret
```

Если ученик понимает этот список, он уже может решать большинство базовых задач курса.
