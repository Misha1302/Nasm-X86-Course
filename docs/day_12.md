# День 12. `cmp`, `test` и условные переходы

## Опора на материалы ВШЭ

`Slides2026-06.pdf`: `CMP`, `TEST`, таблица `Jcc`, signed/unsigned comparisons и GOTO-форма условий.

## Зачем этот день

В C++ ты пишешь:

```cpp
if (x < y) { ... }
```

А в asm это раскладывается на две части:

```text
1. выставить флаги;
2. прыгнуть или не прыгнуть по этим флагам.
```

Сегодня разбираем команды, которые чаще всего стоят перед условными переходами:

```asm
cmp
test
```

И сами переходы:

```asm
je, jne, jl, jg, jb, ja, ...
```

---

## Главная мысль

`cmp a, b` — это как `a - b`, но результат не сохраняется.

`test a, b` — это как `a & b`, но результат не сохраняется.

Обе команды только выставляют флаги.

---

## 1. `cmp`: сравнение через вычитание

```asm
cmp eax, ebx
```

Мысленно:

```text
temp = eax - ebx
temp is not stored
flags are updated
```

Если `eax == ebx`, то:

```text
eax - ebx = 0
ZF = 1
```

Поэтому:

```asm
cmp eax, ebx
je .equal
```

значит:

```cpp
if (eax == ebx) goto equal;
```

---

### Важно: порядок операндов

```asm
cmp eax, ebx
```

это флаги как после:

```text
eax - ebx
```

Не `ebx - eax`.

Поэтому:

```asm
cmp eax, ebx
jl .less
```

означает:

```cpp
if ((int)eax < (int)ebx) goto less;
```

---

## 2. `test`: проверка битов

```asm
test eax, eax
```

Мысленно:

```text
temp = eax & eax
temp is not stored
flags are updated
```

Так как:

```text
eax & eax = eax
```

то `test eax,eax` удобно проверяет, равен ли `eax` нулю.

```asm
test eax, eax
je .zero
```

C++-смысл:

```cpp
if (eax == 0) goto zero;
```

Если нужно проверить конкретный бит:

```asm
test eax, 1
jne .odd
```

Это проверка младшего бита:

```cpp
if (eax & 1) goto odd;
```

---

## 3. Основные переходы

| Переход | Смысл |
|---|---|
| `jmp` | безусловный переход |
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

`jz` и `je` — одно и то же по флагам: оба смотрят на `ZF=1`.

`jnz` и `jne` — тоже одно и то же: смотрят на `ZF=0`.

Разные имена нужны для читаемости:

```asm
cmp eax, ebx
je .equal      ; читается как equal

test eax, eax
jz .zero       ; читается как zero
```

---

## 4. Signed vs unsigned: `jl` не равно `jb`

Один и тот же набор битов:

```text
0xFFFFFFFF
```

как unsigned:

```text
4294967295
```

как signed:

```text
-1
```

Пусть:

```text
eax = 0xFFFFFFFF
ebx = 1
```

Signed-сравнение:

```text
-1 < 1
```

Unsigned-сравнение:

```text
4294967295 > 1
```

Поэтому после:

```asm
cmp eax, ebx
```

для signed будет верна идея:

```asm
jl .less_signed
```

а для unsigned:

```asm
ja .greater_unsigned
```

---

### Как выбрать переход

Если в C++ тип `int`, `short`, `char` как signed — думай про:

```text
jl, jle, jg, jge
```

Если тип `unsigned`, `size_t`, адреса, длины массивов — часто нужны:

```text
jb, jbe, ja, jae
```

Для равенства signed/unsigned не важно:

```text
je, jne
```

Потому что равенство битов одинаковое.

---

## 5. Мини-примеры

### `if (x == y)`

```asm
mov eax, [x]
cmp eax, [y]
je .equal
```

### `if (x != 0)`

```asm
mov eax, [x]
test eax, eax
jne .not_zero
```

### `if ((int)x < (int)y)`

```asm
mov eax, [x]
cmp eax, [y]
jl .less
```

### `if ((unsigned)x < (unsigned)y)`

```asm
mov eax, [x]
cmp eax, [y]
jb .below
```

### `if (x & 8)`

```asm
mov eax, [x]
test eax, 8
jne .bit_is_set
```

---

## 6. Почему `cmp` результат не сохраняет

Сравнение нужно не для того, чтобы получить число `a-b`, а чтобы узнать отношение между числами.

Если бы `cmp` сохранял результат, он портил бы регистры.

```asm
cmp eax, ebx
```

удобен тем, что:

```text
eax и ebx остаются прежними;
флаги обновляются.
```

Это как “примерить вычитание”, но не записывать результат.

---

## 7. Связь с C++ условиями

C++:

```cpp
if (x < y) {
    ans = 1;
}
```

ASM-shape:

```asm
mov eax, [x]
cmp eax, [y]
jge .skip
mov dword [ans], 1
.skip:
```

Почему `jge .skip`, а не `jl .then`?

Оба подхода возможны. В asm часто удобнее прыгнуть через тело, если условие не выполнено.

```text
если x >= y -> пропускаем then
иначе выполняем then
```

---

## 8. Типичная ловушка с флагами

Плохо:

```asm
cmp eax, ebx
add ecx, 1
jl .less
```

`add` поменял флаги. `jl` уже не относится к `cmp`.

Хорошо:

```asm
cmp eax, ebx
jl .less
add ecx, 1
```

Или:

```asm
add ecx, 1
cmp eax, ebx
jl .less
```

---

## 9. Мини-челленджи

#### 1. `cmp eax, ebx` + `je L`

Что значит?

<details>
<summary>Ответ</summary>

```cpp
if (eax == ebx) goto L;
```

</details>

#### 2. `test eax, eax` + `je L`

Что значит?

<details>
<summary>Ответ</summary>

```cpp
if (eax == 0) goto L;
```

</details>

#### 3. `eax=FFFFFFFFh`, `ebx=1`

После:

```asm
cmp eax, ebx
```

какой переход соответствует unsigned `eax > ebx`?

<details>
<summary>Ответ</summary>

`ja`, потому что as unsigned `0xFFFFFFFF > 1`.

</details>

#### 4. Проверка младшего бита

Напиши asm-идею для:

```cpp
if (x & 1) goto odd;
```

<details>
<summary>Ответ</summary>

```asm
mov eax, [x]
test eax, 1
jne .odd
```

</details>

#### 5. Signed меньше

Напиши asm для:

```cpp
if ((int)x < (int)y) goto less;
```

<details>
<summary>Ответ</summary>

```asm
mov eax, [x]
cmp eax, [y]
jl .less
```

</details>

---

## 10. Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| читать `cmp eax, ebx` как `ebx-eax` | порядок именно `eax - ebx` |
| путать `jl` и `jb` | signed `<` против unsigned `<` |
| использовать `jg/ja` без понимания типа | тип сравнения выбирает переход |
| вставить флагоизменяющую команду между `cmp` и `jcc` | переход смотрит уже на другие флаги |
| использовать `cmp eax, 0` там, где проще `test eax,eax` | не ошибка, но `test` идиоматичнее |
| забыть, что `je` и `jz` одно и то же | разные имена для одного флага |

---

## 11. Что должно остаться в голове

После этого дня ты должен уметь:

- объяснить `cmp` как вычитание без сохранения;
- объяснить `test` как `and` без сохранения;
- выбрать `je/jne` для равенства;
- выбрать `jl/jg` для signed;
- выбрать `jb/ja` для unsigned;
- проверить число на ноль через `test eax,eax`;
- проверить бит через `test eax, mask`;
- не портить флаги между `cmp/test` и `jcc`.

Если ты можешь объяснить, почему для `0xFFFFFFFF` одновременно возможны `jl` и `ja` в разных смыслах, день усвоен.
