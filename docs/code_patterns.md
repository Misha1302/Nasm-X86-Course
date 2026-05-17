# Популярные шаблоны кода NASM x86

## Зачем эта страница

Ассемблер проще учить не как набор отдельных инструкций, а как набор стандартных форм.

Почти все учебные задачи собираются из паттернов:

```text
прочитать число;
посчитать выражение;
проверить условие;
сделать цикл;
вызвать функцию;
обратиться к массиву;
вернуть результат.
```

Эта страница — шпаргалка по таким шаблонам.

---

## 1. Минимальная программа

```asm
section .text
global main

main:
    xor eax, eax
    ret
```

Смысл:

```text
return 0;
```

`eax` хранит возвращаемое значение `main`.

---

## 2. `scanf` и `printf`

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

Главное:

```text
scanf получает адрес: x
printf получает значение: [x]
```

---

## 3. Пролог функции

```asm
push ebp
mov ebp, esp
sub esp, N
```

Смысл:

```text
сохранили старый ebp;
создали новый фрейм;
выделили N байт под локальные переменные.
```

Если локальных переменных нет:

```asm
push ebp
mov ebp, esp
```

---

## 4. Эпилог функции

Полная форма:

```asm
mov esp, ebp
pop ebp
ret
```

Короткая форма:

```asm
leave
ret
```

`leave` примерно равно:

```asm
mov esp, ebp
pop ebp
```

---

## 5. Карта фрейма

```text
[ebp+16]  argument 3
[ebp+12]  argument 2
[ebp+8]   argument 1
[ebp+4]   return address
[ebp]     old ebp
[ebp-4]   local variable 1
[ebp-8]   local variable 2
```

Первый аргумент — `[ebp+8]`, потому что `[ebp+4]` занят адресом возврата, а `[ebp]` — старым `ebp`.

---

## 6. Функция `sum(a, b)`

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

Результат лежит в `eax`.

---

## 7. Сохранение callee-saved регистров

Если функция использует `ebx`, `esi`, `edi`, их надо сохранить и восстановить.

```asm
my_func:
    push ebp
    mov ebp, esp

    push ebx
    push esi
    push edi

    ; body

    pop edi
    pop esi
    pop ebx

    pop ebp
    ret
```

Снимать нужно в обратном порядке.

---

## 8. Простой `if`

C++:

```cpp
if (x == 0) {
    y = 1;
}
```

NASM:

```asm
mov eax, [x]
test eax, eax
jne .skip

mov dword [y], 1

.skip:
```

Общий паттерн:

```asm
; check condition
jcc .skip_if_false

; body

.skip_if_false:
```

Часто удобно прыгать по обратному условию, чтобы перепрыгнуть тело.

---

## 9. `if / else`

C++:

```cpp
if (x > y) {
    result = x - y;
} else {
    result = y - x;
}
```

NASM:

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

Главная ошибка: забыть `jmp .end` после then-ветки. Тогда выполнение провалится в `else`.

---

## 10. `while`

C++:

```cpp
while (x != 0) {
    x >>= 1;
}
```

NASM:

```asm
.loop:
    mov eax, [x]
    test eax, eax
    je .end

    shr dword [x], 1
    jmp .loop

.end:
```

Общий паттерн:

```asm
.loop:
    ; check condition
    jcc .end

    ; body

    jmp .loop

.end:
```

---

## 11. `do while`

C++:

```cpp
do {
    x >>= 1;
} while (x != 0);
```

NASM:

```asm
.loop:
    shr dword [x], 1

    mov eax, [x]
    test eax, eax
    jne .loop
```

Отличие:

```text
while    — проверка до тела;
do while — проверка после тела.
```

---

## 12. `for`

C++:

```cpp
for (int i = 0; i < n; ++i) {
    sum += i;
}
```

NASM:

```asm
xor ecx, ecx        ; i = 0
xor eax, eax        ; sum = 0

.loop:
    cmp ecx, [n]
    jge .end

    add eax, ecx

    inc ecx
    jmp .loop

.end:
```

Общий паттерн:

```asm
; init

.loop:
    ; check
    jcc .end

    ; body

    ; update
    jmp .loop

.end:
```

---

## 13. `break` и `continue`

C++:

```cpp
while (...) {
    if (bad) break;
    if (skip) continue;
    body;
}
```

NASM:

```asm
.loop:
    ; loop condition
    jcc .end

    ; if bad -> break
    cmp ...
    je .end

    ; if skip -> continue
    cmp ...
    je .continue

    ; body

.continue:
    ; update if needed
    jmp .loop

.end:
```

Коротко:

```text
break    -> jmp .end
continue -> jmp .continue / .loop
```

---

## 14. Проверка на ноль

```asm
test eax, eax
je .zero
```

или:

```asm
cmp eax, 0
je .zero
```

Идиоматичнее обычно:

```asm
test eax, eax
```

---

## 15. Проверка бита

Нечётность:

```asm
mov eax, [x]
test eax, 1
jne .odd
```

Проверка маски:

```asm
test eax, MASK
jnz .has_bit
```

---

## 16. Signed-сравнение

```asm
mov eax, [x]
cmp eax, [y]
jl .less
jle .less_eq
jg .greater
jge .greater_eq
```

Использовать для `int`, `short`, `signed char`.

---

## 17. Unsigned-сравнение

```asm
mov eax, [x]
cmp eax, [y]
jb .below
jbe .below_eq
ja .above
jae .above_eq
```

Использовать для `unsigned`, размеров и индексов.

---

## 18. `switch` через цепочку сравнений

```asm
cmp eax, 1
je .case1
cmp eax, 2
je .case2
cmp eax, 3
je .case3
jmp .default

.case1:
    ; body
    jmp .end

.case2:
    ; body
    jmp .end

.case3:
    ; body
    jmp .end

.default:
    ; body

.end:
```

Используется для малого количества `case` или разреженных значений.

---

## 19. `switch` через jump table

```asm
cmp eax, 3
ja .default
jmp [.table + 4*eax]

.table:
    dd .case0
    dd .case1
    dd .case2
    dd .case3

.case0:
    ; body
    jmp .end

.case1:
    ; body
    jmp .end

.case2:
    ; body
    jmp .end

.case3:
    ; body
    jmp .end

.default:
    ; body

.end:
```

Если `case` начинаются не с нуля:

```asm
sub eax, MIN_CASE
cmp eax, MAX_CASE - MIN_CASE
ja .default
jmp [.table + 4*eax]
```

---

## 20. Чтение массива `int a[i]`

Если `edx = base`, `ecx = i`:

```asm
mov eax, [edx + 4*ecx]
```

Адрес `&a[i]`:

```asm
lea eax, [edx + 4*ecx]
```

---

## 21. Цикл по массиву

C++:

```cpp
sum = 0;
for (int i = 0; i < n; ++i)
    sum += a[i];
```

NASM:

```asm
xor eax, eax        ; sum = 0
xor ecx, ecx        ; i = 0
mov edx, [a]        ; base pointer, если a — pointer

.loop:
    cmp ecx, [n]
    jge .end

    add eax, [edx + 4*ecx]

    inc ecx
    jmp .loop

.end:
```

---

## 22. Двумерный массив `a[i][j]`

Если `int a[R][C]`:

```text
address = base + 4 * (i*C + j)
```

NASM:

```asm
mov eax, [i]
imul eax, C
add eax, [j]
mov eax, [base + 4*eax]
```

Если base в `edx`:

```asm
mov eax, [i]
imul eax, C
add eax, [j]
mov eax, [edx + 4*eax]
```

---

## 23. Signed division

```asm
mov eax, [x]
cdq
idiv dword [y]
```

После:

```text
eax = x / y
edx = x % y
```

---

## 24. Unsigned division

```asm
mov eax, [x]
xor edx, edx
div dword [y]
```

После:

```text
eax = x / y
edx = x % y
```

---

## 25. Branchless abs

```asm
mov eax, [x]
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
```

Формула:

```cpp
mask = x >> 31;
answer = (x ^ mask) - mask;
```

---

## 26. Masked merge

```asm
mov eax, [a]
and eax, [c]

mov ecx, [c]
not ecx
and ecx, [b]

or eax, ecx
```

Формула:

```cpp
answer = (a & c) | (b & ~c);
```

---

## 27. Упаковка четырёх байтов

```asm
mov eax, [a]
and eax, 255

mov ecx, [b]
and ecx, 255
shl ecx, 8
or eax, ecx

mov ecx, [c]
and ecx, 255
shl ecx, 16
or eax, ecx

mov ecx, [d]
and ecx, 255
shl ecx, 24
or eax, ecx
```

Формула:

```cpp
answer = a | (b << 8) | (c << 16) | (d << 24);
```

---

## 28. Работа с `char` / `short`

Signed `char`:

```asm
movsx eax, byte [x]
```

Unsigned `char`:

```asm
movzx eax, byte [x]
```

Signed `short`:

```asm
movsx eax, word [x]
```

Unsigned `short`:

```asm
movzx eax, word [x]
```

---

## 29. Доступ к полю структуры

Если `edx = r`, и поле `j` лежит по offset 4:

```asm
mov eax, [edx + 4]
```

Если массив `a` внутри структуры начинается по offset 8:

```asm
mov eax, [edx + 8 + 4*ecx]
```

---

## 30. x87: напечатать `float/double`

```asm
finit
fld dword [x]
fld dword [y]
faddp

sub esp, 8
fstp qword [esp]
push fmtFloat
call printf
add esp, 12
```

Важно:

```text
printf("%f") ждёт double, то есть qword.
```

---

## Что выучить первым

Сначала не надо пытаться помнить все 30 шаблонов. Первый уровень:

```text
1. минимальная программа
2. scanf/printf
3. пролог/эпилог
4. карта фрейма
5. вызов функции
6. if
7. if/else
8. while
9. for
10. проверка на ноль
11. signed/unsigned comparison
12. массив a[i]
13. signed division
14. branchless abs
15. masked merge
16. упаковка байтов
```

Этого достаточно, чтобы уверенно стартовать с большинством учебных задач.

## 31. Branchless select

```asm
; eax = a
; edx = b
; ecx = mask: 0 или FFFFFFFFh
and eax, ecx
not ecx
and edx, ecx
or eax, edx
```

Смысл:

```text
mask = FFFFFFFFh -> выбрать a
mask = 00000000h -> выбрать b
```

## 32. Ceil division

Для положительных чисел:

```text
ceil(a / b) = (a + b - 1) / b
```

NASM-shape:

```asm
mov eax, [a]
add eax, [b]
dec eax
xor edx, edx
div dword [b]
```

## 33. Min/max через сравнение

```asm
; eax = current min
; ecx = candidate
cmp ecx, eax
jge .keep
mov eax, ecx
.keep:
```

Для signed-чисел используй signed jumps.

## 34. Recursive function skeleton

```asm
func:
    push ebp
    mov ebp, esp
    sub esp, 4

    ; base case
    ; recursive call

    mov esp, ebp
    pop ebp
    ret
```

## 35. Decimal reverse

```text
rev = 0
while x != 0:
    digit = x % 10
    rev = rev * 10 + digit
    x /= 10
```

## 36. GCD

```text
while b != 0:
    r = a % b
    a = b
    b = r
```

## 37. libc call checklist

- аргументы справа налево;
- адрес строки, не `[строка]`;
- caller clean-up;
- `eax/ecx/edx` могут быть испорчены;
- для Spring-04 проверить 16-byte alignment.
