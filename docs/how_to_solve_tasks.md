# Как решать задачи на NASM

Эта страница — алгоритм решения. Её нужно открыть, когда условие уже есть, а в голове пока хаос.

## Алгоритм

1. Напиши C++-идею.
2. Убери лишний синтаксис C++ и оставь low-level shape.
3. Выбери регистры.
4. Напиши NASM-фрагмент вычисления.
5. Добавь `scanf` / `printf`, если задача требует ввод/вывод.
6. Проверь стек после каждого `call`.
7. Проверь 2–3 обычных теста.
8. Проверь крайние случаи.
9. Только потом сдавай.

---

## Шаг 1. C++-идея

Не начинай с NASM. Сначала запиши, что ты считаешь.

Пример:

```cpp
answer = a * b + c;
```

Если C++-идея сложная, NASM почти наверняка получится случайным.

---

## Шаг 2. Low-level shape

Разложи выражение на простые действия:

```text
load a
multiply by b
add c
print answer
```

Для условия:

```cpp
if (x < y) answer = 1;
```

shape будет таким:

```text
load x
compare with y
if x >= y -> skip
answer = 1
```

---

## Шаг 3. Выбор регистров

Для первых задач чаще всего хватает:

| Регистр | Роль |
|---|---|
| `eax` | главный результат |
| `ecx` | временное значение / счётчик |
| `edx` | деление, остаток, временное значение |

Не используй `ebx`, `esi`, `edi` как обычные временные регистры в полной функции, пока не умеешь сохранять их. В CDECL они callee-saved.

---

## Шаг 4. NASM-фрагмент

C++:

```cpp
answer = a * b + c;
```

NASM:

```asm
mov eax, [a]
imul eax, [b]
add eax, [c]
```

Проверка по смыслу:

```text
eax = a
eax = eax * b
eax = eax + c
```

---

## Шаг 5. Ввод и вывод

Шаблон чтения одного `int`:

```asm
push x
push fmtIn
call scanf
add esp, 8
```

Шаблон печати результата из `eax`:

```asm
push eax
push fmtOut
call printf
add esp, 8
```

Главная ловушка:

| C | NASM |
|---|---|
| `scanf("%d", &x)` | `push x` |
| `printf("%d", x)` | `push dword [x]` |

---

## Шаг 6. Проверка стека

После каждого CDECL-вызова убирай аргументы:

| Вызов | Сколько убрать |
|---|---:|
| `f(a)` | `add esp, 4` |
| `f(a, b)` | `add esp, 8` |
| `f(a, b, c)` | `add esp, 12` |
| `printf("%d", x)` | `add esp, 8` |
| `scanf("%d%d", &a, &b)` | `add esp, 12` |

Если стек не сбалансирован, ошибка может проявиться не сразу.

---

## Шаг 7. Ручные тесты

Для каждой задачи нужны три типа тестов.

| Тип | Пример |
|---|---|
| Обычный | `a=2, b=3` |
| Ноль / граница | `x=0`, `month=1` |
| Опасный смысл | отрицательное число, максимум маски, деление |

Пример для branchless abs:

| `x` | expected |
|---:|---:|
| `0` | `0` |
| `1` | `1` |
| `-1` | `1` |
| `123` | `123` |
| `-123` | `123` |

---

## Мини-пример целиком

Задача: прочитать `a`, `b`, `c`, вывести `a*b+c`.

```asm
section .data
    fmtIn db "%d", 0
    fmtOut db "%d", 10, 0

section .bss
    a resd 1
    b resd 1
    c resd 1

section .text
    extern scanf
    extern printf
    global main

main:
    push a
    push fmtIn
    call scanf
    add esp, 8

    push b
    push fmtIn
    call scanf
    add esp, 8

    push c
    push fmtIn
    call scanf
    add esp, 8

    mov eax, [a]
    imul eax, [b]
    add eax, [c]

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

---

## Чеклист перед сдачей

- [ ] Я понимаю C++-идею задачи.
- [ ] Я знаю, где результат: в `eax`, `edx` или памяти.
- [ ] Я не перепутал `x` и `[x]`.
- [ ] После каждого `call` есть правильный `add esp, ...`.
- [ ] Для `idiv` есть `cdq`.
- [ ] Для `div` есть `xor edx, edx`.
- [ ] Для signed/unsigned comparison выбран правильный jump.
- [ ] Я проверил минимум 3 теста руками.
