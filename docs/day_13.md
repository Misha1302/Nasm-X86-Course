# День 13. `if`, циклы и GOTO-форма

## Опора на материалы ВШЭ

`Slides2026-06.pdf`: GOTO-форма, `if/else`, циклы, `do while`, пример popcount и связь условий с `cmp/test/jcc`.

## Зачем этот день

В C++ у тебя есть красивые конструкции:

```cpp
if
while
for
do while
break
continue
```

В asm их нет.

И это не значит, что asm “бедный”. Просто процессору достаточно более простых вещей:

```text
метка
условный переход
безусловный переход
```

Сегодня мы учимся видеть за C++-конструкциями обычную GOTO-форму.

---

## Главная мысль

Управляющие конструкции C/C++ раскладываются в:

```asm
cmp / test
jcc
jmp
labels
```

То есть:

```text
условие -> флаги -> переход -> метка
```

---

# 1. Метки и `jmp`

Метка — это имя адреса в коде.

```asm
.loop:
    ; some code
    jmp .loop
```

`jmp` — безусловный переход.

```asm
jmp .end
```

значит:

```text
следующая инструкция будет по адресу .end
```

В C++ это ближе всего к:

```cpp
goto end;
```

---

# 2. Простой `if`

C++:

```cpp
if (x == 0) {
    y = 1;
}
```

ASM-shape:

```asm
mov eax, [x]
test eax, eax
jne .skip

mov dword [y], 1

.skip:
```

Почему `jne .skip`?

Мы хотим выполнить тело только если `x == 0`.

Значит, если `x != 0`, надо перепрыгнуть через тело.

```text
if not condition -> jump over body
body
skip:
```

Это очень частая форма.

---

# 3. `if/else`

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
mov eax, [x]
cmp eax, [y]
jle .else

.then:
    mov eax, [x]
    sub eax, [y]
    mov [result], eax
    jmp .end

.else:
    mov eax, [y]
    sub eax, [x]
    mov [result], eax

.end:
```

Главный трюк:

```asm
jmp .end
```

после then-ветки.

Если его забыть, выполнение “провалится” в else, и else тоже выполнится.

---

## Почему иногда прыгают по обратному условию

В C++:

```cpp
if (x > y) {
    then_body;
}
```

В asm часто пишут:

```asm
cmp x, y
jle .skip
; then_body
.skip:
```

То есть если условие не выполнено, прыгаем через тело.

Это нормально. Не пытайся искать дословное `jg`, если в коде может быть `jle`.

---

# 4. `while`

C++:

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

Структура:

```text
.loop:
    проверить условие
    если условие ложное -> .end
    тело
    jmp .loop
.end:
```

---

# 5. `do while`

C++:

```cpp
do {
    x >>= 1;
} while (x != 0);
```

ASM-shape:

```asm
.loop:
    shr eax, 1
    test eax, eax
    jne .loop
```

Отличие от `while`:

```text
while    -> сначала проверка, потом тело
do while -> сначала тело, потом проверка
```

Поэтому `do while` всегда выполняет тело хотя бы один раз.

---

# 6. `for`

C++:

```cpp
for (int i = 0; i < n; ++i) {
    sum += i;
}
```

GOTO-форма:

```cpp
i = 0;
goto check;

loop:
    sum += i;
    ++i;

check:
    if (i < n) goto loop;
```

ASM-shape:

```asm
xor ecx, ecx        ; i = 0
xor eax, eax        ; sum = 0

.check:
    cmp ecx, [n]
    jge .end

    add eax, ecx
    inc ecx
    jmp .check

.end:
```

Здесь:

```text
ecx = i
eax = sum
```

---

# 7. `break` и `continue`

C++:

```cpp
while (...) {
    if (bad) break;
    if (skip) continue;
    body;
}
```

ASM-идея:

```asm
.loop:
    ; check loop condition
    je .end

    ; if bad -> break
    cmp ...
    je .end

    ; if skip -> continue
    cmp ...
    je .loop

    ; body
    jmp .loop

.end:
```

`break` — это `jmp` на конец цикла.

`continue` — это `jmp` на проверку или следующую итерацию.

---

# 8. Popcount-пример

Задача: посчитать количество единичных битов в числе.

C++:

```cpp
int result = 0;
while (x != 0) {
    result += x & 1;
    x >>= 1;
}
```

ASM:

```asm
xor ecx, ecx        ; result = 0

.loop:
    test edx, edx   ; x == 0?
    je .end

    mov eax, edx
    and eax, 1
    add ecx, eax

    shr edx, 1
    jmp .loop

.end:
```

Роли регистров:

```text
edx = x
ecx = result
eax = temporary x & 1
```

Разбор одной итерации:

```asm
mov eax, edx  ; скопировали x
and eax, 1    ; оставили младший бит
add ecx, eax  ; прибавили его к result
shr edx, 1    ; x >>= 1
```

---

# 9. Как читать чужой asm с циклами

Смотри не на конкретные имена меток, а на форму.

## Признак `while`

```asm
.loop:
    check
    jump_to_end_if_false
    body
    jmp .loop
.end:
```

## Признак `do while`

```asm
.loop:
    body
    check
    jump_to_loop_if_true
```

## Признак `if/else`

```asm
    check
    jump_to_else_if_false
.then:
    then_body
    jmp end
.else:
    else_body
.end:
```

---

# 10. Мини-челленджи

### 1. Перепиши `if/else`

C++:

```cpp
if (x == 0)
    y = 1;
else
    y = 2;
```

Напиши GOTO-форму.

<details>
<summary>Один вариант</summary>

```asm
mov eax, [x]
test eax, eax
jne .else

mov dword [y], 1
jmp .end

.else:
mov dword [y], 2

.end:
```

</details>

### 2. `while (x > 0) x--;`

<details>
<summary>Один вариант</summary>

```asm
.loop:
    cmp dword [x], 0
    jle .end
    dec dword [x]
    jmp .loop
.end:
```

</details>

### 3. Сумма от 1 до n

Напиши идею цикла.

<details>
<summary>Один вариант</summary>

```asm
mov ecx, 1      ; i
xor eax, eax    ; sum

.loop:
    cmp ecx, [n]
    jg .end
    add eax, ecx
    inc ecx
    jmp .loop
.end:
```

</details>

### 4. Узнай форму

```asm
.loop:
    shr eax, 1
    test eax, eax
    jne .loop
```

Это больше похоже на `while` или `do while`?

<details>
<summary>Ответ</summary>

На `do while`, потому что тело выполняется до проверки.

</details>

---

# 11. Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| забыть `jmp .end` после then-ветки | выполнение провалится в else |
| перепутать условие и обратное условие | тело выполнится не тогда |
| забыть `jmp .loop` в конце while | цикл выполнится один раз |
| поставить проверку не там | `while` превратится в `do while` или наоборот |
| портить регистр-счётчик внутри тела | цикл ломается |
| забыть обновление счётчика | бесконечный цикл |

---

# 12. Что должно остаться в голове

После этого дня ты должен уметь:

- объяснить, почему в asm нет настоящего `if`, а есть переходы;
- написать GOTO-форму `if`, `if/else`, `while`, `do while`, `for`;
- понимать `break` и `continue` как `jmp`;
- читать popcount-цикл;
- узнавать форму цикла по расположению проверки.

Если ты можешь превратить простой C++-цикл в метки и переходы, день усвоен.
