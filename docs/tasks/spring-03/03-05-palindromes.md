# 03-5. Палиндромы

## Условие

Даны unsigned 32-bit число `M` и неотрицательное число `N`.

Нужно выполнить ровно `N` шагов:

```text
M = M + reverse_decimal(M)
```

После этого проверить, стал ли результат палиндромом.

Если да — вывести `Yes` и число. Иначе вывести `No`.

Массивы запрещены. Нужно сделать вспомогательную функцию разворота числа.

## Ввод

```text
M N
```

## Вывод

Если после ровно `N` шагов палиндром:

```text
Yes
value
```

Иначе:

```text
No
```

## Ограничения

- `M` — unsigned 32-bit;
- переполнений в промежуточных вычислениях не возникает;
- массивы запрещены.

## Решение

Нужна функция:

```text
reverse_decimal(x)
```

Она разворачивает десятичную запись числа без массива:

```text
rev = 0
while x != 0:
    digit = x % 10
    rev = rev * 10 + digit
    x = x / 10
```

Проверка палиндрома:

```text
x == reverse_decimal(x)
```

## Алгоритм

```text
read M, N

repeat N times:
    r = reverse_decimal(M)
    M = M + r

if M == reverse_decimal(M):
    print Yes
    print M
else:
    print No
```

Важно: даже если палиндром появился раньше, всё равно выполняем ровно `N` шагов.

## NASM-shape для reverse

```asm
; input:  [ebp+8] = x
; output: eax = reversed

xor esi, esi        ; rev = 0
mov eax, [ebp+8]    ; x

.loop:
    test eax, eax
    je .done

    xor edx, edx
    mov ecx, 10
    div ecx          ; eax = x / 10, edx = digit

    imul esi, esi, 10
    add esi, edx
    jmp .loop

.done:
    mov eax, esi
```

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| остановиться раньше `N` | условие требует проверять результат ровно после `N` шагов |
| использовать массив цифр | массивы запрещены |
| забыть `xor edx, edx` перед `div 10` | деление сломается |
| потерять `M` после вызова reverse | `eax/ecx/edx` caller-saved |

## Где в курсе

- [День 09 — деление](/day_09)
- [День 17 — CDECL](/day_17)
- [Десятичные алгоритмы](/patterns/decimal)
