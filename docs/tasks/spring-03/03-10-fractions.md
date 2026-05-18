# 03-10. Дроби

## Условие

Дано `N` несократимых дробей `Xi / Yi`. Нужно вывести их сумму как несократимую дробь.

## Ввод

```text
N
X1 Y1
X2 Y2
...
XN YN
```

## Вывод

```text
numerator denominator
```

## Ограничения

- `N <= 12`;
- `Xi, Yi <= 20`;
- числитель и знаменатель ответа помещаются в 32-bit.

## Решение

Храним текущую сумму как дробь:

```text
num / den
```

Начальное значение:

```text
0 / 1
```

Добавление дроби `x / y`:

```text
num = num * y + x * den
den = den * y
```

После каждого добавления можно сокращать дробь через `gcd(num, den)`. Это уменьшает риск больших промежуточных значений.

## GCD

Алгоритм Евклида:

```text
while b != 0:
    r = a % b
    a = b
    b = r
return a
```

## Алгоритм

```text
read N
num = 0
den = 1

repeat N times:
    read x, y
    num = num * y + x * den
    den = den * y

    g = gcd(num, den)
    num /= g
    den /= g

print num, den
```

## NASM-shape

Для сложения:

```asm
; eax = num * y
mov eax, [num]
imul eax, [y]

; ecx = x * den
mov ecx, [x]
imul ecx, [den]

add eax, ecx
mov [num], eax

mov eax, [den]
imul eax, [y]
mov [den], eax
```

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| складывать числители и знаменатели отдельно | так дроби не складываются |
| не сокращать результат | требуется несократимая дробь |
| забыть `edx` перед делением в gcd | `div/idiv` использует `edx:eax` |
| использовать floating point | ответ должен быть точной дробью |

## Где в курсе

- [День 09 — деление](/day_09)
- [Десятичные алгоритмы](/patterns/decimal)
