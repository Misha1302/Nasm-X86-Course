# `double` через x87 FPU в NASM

Эта страница объясняет, как писать NASM-функции для C-программы, если функция принимает `double`, считает выражение через x87 FPU и возвращает `double` обратно в C.

Цель — уметь реализовать функции вида:

```c
extern double f1(double x);
extern double f2(double x);
extern double f3(double x);
```

Например, для задания с вычислением площади фигуры функции `f1`, `f2`, `f3` пишутся на NASM, а `root`, `integral` и основная логика остаются на C.

---

## Главная идея

Для обычных целых чисел мы привыкли к регистрам:

```text
eax, ebx, ecx, edx
```

Но `double` через x87 считается не в `eax`, а в специальных вещественных регистрах:

```text
st0, st1, st2, st3, st4, st5, st6, st7
```

Формально это регистры, но работать с ними нужно как со стеком:

```text
st0 — вершина FPU-стека
st1 — значение под вершиной
st2 — следующее значение
...
```

Коротко:

```text
fld    -> положить число на вершину FPU-стека
faddp  -> сложить верхние значения и снять одно
fmulp  -> умножить верхние значения и снять одно
fstp   -> сохранить значение и снять его со стека
```

Важно: это не стек в памяти. Это стековая организация специальных FPU-регистров.

---

## Как `double x` передаётся в 32-bit cdecl

В 32-битном `cdecl` аргументы функции лежат в обычном стеке памяти.

Для функции:

```c
double f(double x);
```

после стандартного пролога:

```asm
push ebp
mov ebp, esp
```

стек выглядит так:

```text
[ebp + 0]  старое значение ebp
[ebp + 4]  адрес возврата
[ebp + 8]  первый аргумент функции: double x
```

`double` занимает 8 байт, поэтому его нужно читать как `qword`:

```asm
fld qword [ebp + 8]
```

Эта команда загружает `x` в `st0`.

---

## Как вернуть `double` в C

В 32-bit cdecl значение типа `double` возвращается через вершину FPU-стека `st0`.

Значит, перед `ret` в `st0` должен лежать результат функции.

Минимальный пример — функция, которая возвращает свой аргумент:

```asm
section .text
    global identity

identity:
    push ebp
    mov ebp, esp

    fld qword [ebp + 8]    ; st0 = x

    mov esp, ebp
    pop ebp
    ret
```

Со стороны C:

```c
extern double identity(double x);
```

---

## Базовые команды x87 для задания

### Загрузка

```asm
fld qword [x]
```

Положить `double` из памяти на вершину FPU-стека.

```asm
fld1
```

Положить константу `1.0`.

```asm
fld st0
```

Продублировать верхнее значение стека.

---

### Сложение и умножение

```asm
faddp st1, st0
```

Сложить `st1 + st0`, оставить результат и снять один элемент со стека.

```asm
fmulp st1, st0
```

Умножить `st1 * st0`, оставить результат и снять один элемент со стека.

---

### Вычитание и деление

С ними нужно быть внимательнее, потому что порядок операндов важен.

Шаблон для `a - b`:

```asm
fld qword [a]
fld qword [b]
fsubp st1, st0        ; st1 = st1 - st0, pop -> st0 = a - b
```

Шаблон для `a / b`:

```asm
fld qword [a]
fld qword [b]
fdivp st1, st0        ; st1 = st1 / st0, pop -> st0 = a / b
```

Есть и формы с операндом из памяти:

```asm
fsub qword [value]    ; st0 = st0 - value
fdiv qword [value]    ; st0 = st0 / value
```

---

## Шаблон NASM-функции `double f(double x)`

```asm
section .text
    global f

f:
    push ebp
    mov ebp, esp

    ; здесь вычисляем ответ и оставляем его в st0
    fld qword [ebp + 8]

    mov esp, ebp
    pop ebp
    ret
```

Правило для проверки:

> В конце функции на FPU-стеке должно остаться ровно одно важное значение — результат в `st0`.

Если временные значения не сняты со стека, следующая операция может получить мусор или переполнить x87-стек.

---

## Пример 1. `f3(x) = (1 - x) / 3`

```asm
section .data
    three dq 3.0

section .text
    global f3

f3:
    push ebp
    mov ebp, esp

    fld1                    ; st0 = 1
    fsub qword [ebp + 8]    ; st0 = 1 - x
    fdiv qword [three]      ; st0 = (1 - x) / 3

    mov esp, ebp
    pop ebp
    ret
```

Здесь всё просто:

```text
fld1                  -> st0 = 1
fsub qword [ebp + 8]  -> st0 = 1 - x
fdiv qword [three]    -> st0 = (1 - x) / 3
```

---

## Пример 2. `f2(x) = x^5`

```asm
section .text
    global f2

f2:
    push ebp
    mov ebp, esp

    fld qword [ebp + 8]     ; st0 = x
    fld st0                 ; st0 = x,   st1 = x
    fmul st0, st0           ; st0 = x^2, st1 = x
    fmul st0, st0           ; st0 = x^4, st1 = x
    fmulp st1, st0          ; st0 = x^5

    mov esp, ebp
    pop ebp
    ret
```

Пошагово:

```text
st0 = x
st0 = x,   st1 = x
st0 = x^2, st1 = x
st0 = x^4, st1 = x
st0 = x^5
```

---

## Пример 3. `f1(x) = 2^x + 1`

Для `2^x` нет одной простой команды. У x87 есть команда:

```asm
f2xm1
```

Она считает:

```text
2^y - 1
```

но её удобно применять к дробной части аргумента.

Идея такая:

```text
x = integer_part + fractional_part
2^x = 2^integer_part * 2^fractional_part
```

Код:

```asm
section .text
    global f1

f1:
    push ebp
    mov ebp, esp

    fld qword [ebp + 8]     ; st0 = x
    fld st0                 ; st0 = x, st1 = x
    frndint                 ; st0 = rounded integer part, st1 = x
    fxch st1                ; st0 = x, st1 = integer part
    fsub st0, st1           ; st0 = fractional part, st1 = integer part
    f2xm1                   ; st0 = 2^fractional - 1
    fld1                    ; st0 = 1, st1 = 2^fractional - 1, st2 = integer part
    faddp st1, st0          ; st0 = 2^fractional, st1 = integer part
    fscale                  ; st0 = 2^fractional * 2^integer = 2^x
    fstp st1                ; убрать integer part со стека
    fld1                    ; st0 = 1, st1 = 2^x
    faddp st1, st0          ; st0 = 2^x + 1

    mov esp, ebp
    pop ebp
    ret
```

`fscale` умножает `st0` на `2^st1`.

После `fscale` в стеке остаётся лишнее значение с целой частью. Его нужно убрать:

```asm
fstp st1
```

Иначе функция вернёт правильный результат в `st0`, но оставит мусор на FPU-стеке.

---

## Полный пример файла `funcs.asm`

```asm
section .data
    three dq 3.0

section .text
    global f1
    global f2
    global f3

; double f1(double x) = 2^x + 1
f1:
    push ebp
    mov ebp, esp

    fld qword [ebp + 8]
    fld st0
    frndint
    fxch st1
    fsub st0, st1
    f2xm1
    fld1
    faddp st1, st0
    fscale
    fstp st1
    fld1
    faddp st1, st0

    mov esp, ebp
    pop ebp
    ret

; double f2(double x) = x^5
f2:
    push ebp
    mov ebp, esp

    fld qword [ebp + 8]
    fld st0
    fmul st0, st0
    fmul st0, st0
    fmulp st1, st0

    mov esp, ebp
    pop ebp
    ret

; double f3(double x) = (1 - x) / 3
f3:
    push ebp
    mov ebp, esp

    fld1
    fsub qword [ebp + 8]
    fdiv qword [three]

    mov esp, ebp
    pop ebp
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
```

---

## Как вызвать эти функции из C

```c
#include <stdio.h>

extern double f1(double x);
extern double f2(double x);
extern double f3(double x);

int main(void)
{
    double x = 2.0;

    printf("f1(%f) = %f\n", x, f1(x));
    printf("f2(%f) = %f\n", x, f2(x));
    printf("f3(%f) = %f\n", x, f3(x));

    return 0;
}
```

Сборка для Linux IA-32:

```bash
nasm -f elf32 funcs.asm -o funcs.o
gcc -m32 -no-pie main.c funcs.o -lm -o main
./main
```

`-m32` нужен, потому что код использует 32-битный `cdecl` и аргумент по адресу `[ebp + 8]`.

---

## Частые ошибки

| Ошибка | Что происходит |
|---|---|
| Использовать `eax` для `double` | x87 возвращает `double` через `st0`, а не через `eax` |
| Загрузить `double` как `dword` | прочитаются только 4 байта вместо 8 |
| Забыть снять временное значение | FPU-стек засоряется лишними элементами |
| Перепутать порядок `fsubp` / `fdivp` | получится другой знак или обратная дробь |
| Пытаться вернуть результат через память без `st0` | C-код не получит возвращаемое значение функции |
| Собирать как x64 | `[ebp + 8]` и 32-bit cdecl уже не соответствуют ABI |

---

## Мини-чеклист для задания

Перед сдачей проверь:

- каждая функция объявлена через `global`;
- C-код объявляет её через `extern double f(double x);`;
- аргумент читается как `fld qword [ebp + 8]`;
- результат перед `ret` лежит в `st0`;
- лишние значения сняты с FPU-стека;
- файл собирается через `nasm -f elf32`;
- C-код собирается через `gcc -m32`;
- на Linux добавлена секция `.note.GNU-stack`.

---

## Что сказать на защите

Короткая формулировка:

> Вещественные вычисления выполняются через x87 FPU. Это специальные регистры `st0..st7`, организованные как стек. В 32-bit cdecl аргумент `double x` передаётся через стек памяти и читается как `qword [ebp + 8]`. Результат функции типа `double` должен остаться в `st0`, потому что именно через вершину FPU-стека C-код получает возвращаемое вещественное значение.
