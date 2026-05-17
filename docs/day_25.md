# День 25. Финальная сборка: что ты реально умеешь

## Опора на материалы ВШЭ

Все пройденные темы курса: IA-32, NASM, секции, ввод/вывод, арифметика, биты, флаги, переходы, адресация, стек, CDECL, reverse engineering, структуры, безопасность, floating point, x87 и C++ object model. Отдельный приоритет — задачи 01-7…01-10.

## Зачем этот день

Последний день — не новая теория.

Это день честной проверки: не “я вроде читал”, а “я могу объяснить, написать, нарисовать и не сломать стек”.

Хорошая готовность к экзамену выглядит так:

```text
решаю маленькую задачу;
читаю asm-фрагмент;
рисую стек/регистры/память;
объясняю, почему код работает;
нахожу типовую ошибку.
```

---

## Главная мысль

Ты понял тему, если можешь объяснить её другу на листочке с одной схемой.

Если схема не рисуется — тему надо повторить.

---

## 1. Карта курса

| Блок | Что должен уметь |
|---|---|
| Машина | объяснить CPU, регистры, память, инструкции |
| NASM | собрать программу в SASM и из CLI |
| Память | отличать `x` и `[x]`, понимать секции и endian |
| Арифметика | `add/sub/imul`, `div/idiv`, `cdq`, остаток в `edx` |
| Биты | `and/or/xor/not`, `shl/shr/sar`, маски |
| Флаги | `ZF/SF/CF/OF`, `cmp`, `test`, `jcc` |
| Control flow | `if/while/for/switch` как метки и переходы |
| Адресация | `[base+index*scale+offset]`, `lea`, массивы |
| Стек | `push/pop/call/ret`, рост вниз, баланс `esp` |
| CDECL | `[ebp+8]`, `[ebp-4]`, `eax` return, caller/callee-saved |
| Reverse | восстановить возможный C-смысл |
| Structs | offsets, padding, alignment |
| Security | buffer overflow, canary, ASLR, DEP/NX на уровне идеи |
| Floating point | binary fractions, NaN/Inf, approximation |
| x87 | stack model, `fld/fstp/faddp`, `%f` как `double` |
| C++ objects | hidden `this`, `vptr`, vtable |

---

## 2. Что обязательно перед экзаменом

Если времени мало, повторяй в таком порядке:

1. `x` vs `[x]`.
2. `scanf/printf` и порядок `push`.
3. `div/idiv`, `cdq`, `edx:eax`.
4. Битовые задачи 01-7…01-10.
5. `cmp/test/jcc`, signed vs unsigned.
6. `push/pop/call/ret`.
7. Фрейм `[ebp+8]`, `[ebp-4]`.
8. `lea` и адресация массивов.
9. Structures offsets.
10. Reverse engineering маленьких функций.

Это ядро. Если оно крепкое, остальное уже добирается легче.

---

## 3. Быстрый чеклист домашек 01-7…01-10

### 01-7. Упаковка вектора

Формула:

```cpp
x = a | (b << 8) | (c << 16) | (d << 24);
```

Картинка:

```text
31..24      23..16      15..8       7..0
+-----------+-----------+-----------+-----------+
|     d     |     c     |     b     |     a     |
+-----------+-----------+-----------+-----------+
```

Команды:

```asm
shl
or
and ; если надо ограничить байт
```

Проверка:

```text
1 2 3 4 -> 0x04030201
```

### 01-8. Masked merge

Формула:

```cpp
d = (a & c) | (b & ~c);
```

Крайние тесты:

```text
c = 0          -> answer = b
c = FFFFFFFFh  -> answer = a
```

### 01-9. Модуль числа без переходов

Формула:

```cpp
mask = x >> 31;
ans = (x ^ mask) - mask;
```

NASM:

```asm
mov eax, [x]
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
```

Главная ловушка:

```text
нужен sar, не shr
```

### 01-10. Год на Пандоре

Формула:

```cpp
before = month - 1;
answer = before * 41 + before / 2 + day;
```

NASM:

```asm
mov eax, [month]
sub eax, 1
mov ecx, eax
imul eax, 41
shr ecx, 1
add eax, ecx
add eax, [day]
```

---

::: tip Про вывод битовых ответов
Если задача битовая и ответ проверяется как unsigned 32-bit, используй `%u`, а не `%d`:

```asm
fmtOut db "%u", 10, 0
```

Для signed-арифметики оставляем `%d`.
:::

## 4. Mock exam на 90 минут

### Часть A. Написать код / формулу

#### A1. Упаковка байтов

Даны `a,b,c,d`. Напиши формулу и NASM-идею для упаковки в `d c b a`.

<details>
<summary>Ответ</summary>

```cpp
x = a | (b << 8) | (c << 16) | (d << 24);
```

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

</details>

#### A2. Masked merge

Даны `a,b,c`. Выбрать биты из `a`, где `c=1`, иначе из `b`.

<details>
<summary>Ответ</summary>

```cpp
d = (a & c) | (b & ~c);
```

</details>

#### A3. Branchless abs

Напиши `abs(x)` без `jcc` и `cmov`.

<details>
<summary>Ответ</summary>

```asm
mov eax, [x]
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
```

</details>

#### A4. Пандора

Напиши формулу для номера дня.

<details>
<summary>Ответ</summary>

```cpp
before = month - 1;
answer = before * 41 + before / 2 + day;
```

</details>

---

### Часть B. Прочитать код

#### B1. `cmp` и signed/unsigned

```asm
cmp eax, ebx
jl .L1
jb .L2
```

Объясни разницу `jl` и `jb`.

<details>
<summary>Ответ</summary>

`jl` — signed `<`, смотрит на signed-отношение через `SF/OF`.

`jb` — unsigned `<`, смотрит на borrow/carry через `CF`.

Для одних и тех же битов результат может отличаться.

</details>

#### B2. `test`

```asm
test eax, eax
je .zero
```

Что это значит?

<details>
<summary>Ответ</summary>

Проверка `eax == 0`. `test eax,eax` обновляет флаги как `eax & eax`, не меняя `eax`.

</details>

#### B3. Адресация

```asm
lea eax, [edx + 4*ecx + 8]
```

Что делает эта строка?

<details>
<summary>Ответ</summary>

Считает адрес/выражение `edx + 4*ecx + 8` и кладёт в `eax`. Память не читает.

</details>

#### B4. Массив

```asm
mov eax, [edx + 4*ecx]
```

Возможный C-смысл?

<details>
<summary>Ответ</summary>

Если `edx` — база `int`-массива, `ecx` — индекс, то:

```cpp
eax = a[i];
```

</details>

---

### Часть C. Стек и функции

#### C1. Нарисуй фрейм

Функция имеет два аргумента и две локальные `int`-переменные. Нарисуй расположение относительно `ebp`.

<details>
<summary>Ответ</summary>

```text
[ebp+12]  argument 2
[ebp+8]   argument 1
[ebp+4]   return address
[ebp]     old ebp
[ebp-4]   local 1
[ebp-8]   local 2
```

</details>

#### C2. Напиши `sum`

```c
int sum(int a, int b) { return a + b; }
```

<details>
<summary>Ответ</summary>

```asm
sum:
    push ebp
    mov ebp, esp

    mov eax, [ebp+8]
    add eax, [ebp+12]

    pop ebp
    ret
```

</details>

#### C3. Вызови `sum(a,b)`

<details>
<summary>Ответ</summary>

```asm
push dword [b]
push dword [a]
call sum
add esp, 8
```

Результат в `eax`.

</details>

---

### Часть D. Reverse engineering

#### D1. Восстанови смысл

```asm
mov eax, [ebp+8]
add eax, [ebp+12]
ret
```

<details>
<summary>Ответ</summary>

Возможный C-смысл:

```cpp
int f(int a, int b)
{
    return a + b;
}
```

</details>

#### D2. Указатель

```asm
mov eax, [ebp+8]
mov edx, [ebp+12]
mov [eax], edx
ret
```

<details>
<summary>Ответ</summary>

Первый аргумент похож на указатель:

```cpp
void f(int* p, int x)
{
    *p = x;
}
```

Точный тип может зависеть от контекста.

</details>

#### D3. Маленький тип

```asm
movsx eax, byte [ebp+8]
ret
```

<details>
<summary>Ответ</summary>

Первый аргумент/значение читается как signed byte, возможный тип `signed char`, возвращается как `int`.

</details>

---

### Часть E. Объяснить словами

#### E1. Что делает canary?

<details>
<summary>Ответ</summary>

Canary — защитное значение между локальным буфером и служебными данными фрейма. Перед возвратом функция проверяет, не изменился ли canary. Если изменился — вероятно, было переполнение буфера.

</details>

#### E2. Почему `printf("%f")` ждёт `qword`?

<details>
<summary>Ответ</summary>

В variadic C-функциях `float` продвигается до `double`, а `double` занимает 8 байт. Поэтому для `%f` нужно передавать `qword`.

</details>

#### E3. Что такое hidden `this`?

<details>
<summary>Ответ</summary>

Это скрытый параметр метода: адрес объекта, для которого вызван метод.

</details>

---

## 5. Таблица типовых провалов

| Симптом | Что повторить |
|---|---|
| путаешь `x` и `[x]` | день 05 |
| ломается `scanf` | дни 05–06, CDECL-аргументы |
| деление даёт мусор | дни 08–09: `cdq`, `edx:eax` |
| не понимаешь `jl`/`jb` | дни 11–12: flags, signed/unsigned |
| не можешь написать цикл | день 13 |
| не понимаешь `[eax+4*ecx+8]` | день 15 |
| путаешь `[ebp+8]` | дни 16–17 |
| не видишь pointer в asm | день 18 |
| не умеешь считать поля структуры | день 19 |
| не понимаешь canary | день 21 |
| x87 печатает мусор | дни 22–23 |

---

## 6. Последняя проверка “на листочке”

Без компьютера нарисуй:

1. `EAX/AX/AH/AL`.
2. `.text/.data/.bss`.
3. `x` vs `[x]`.
4. `edx:eax / operand`.
5. `cmp = subtraction without storing`.
6. `if/else` через `jcc` и `jmp`.
7. стек после `call`.
8. фрейм с `[ebp+8]`, `[ebp-4]`.
9. `[base+index*scale+offset]`.
10. структуру с padding.

Если все 10 схем рисуются уверенно — база реально есть.

---

## 7. Финальный принцип

Ассемблер становится понятным не тогда, когда ты выучил 100 команд.

Он становится понятным, когда ты видишь движение данных:

```text
memory -> register -> operation -> flags / memory / stack
```

И можешь честно ответить на вопросы:

```text
где лежит значение?
какого оно размера?
это адрес или данные?
какая инструкция меняет флаги?
куда прыгнет управление?
кто чистит стек?
что будет в eax перед ret?
```

Если эти вопросы стали привычными, ты уже не “боишься NASM”, а читаешь его как нормальный низкоуровневый язык.
