# 03-18. Знаковое произведение

## Условие

Даны три signed 32-bit числа `a`, `b`, `c`.

Нужно вывести их произведение в десятичной системе без лидирующих нулей.

## Ввод

```text
a b c
```

## Вывод

Одно десятичное число.

## Ограничения

- `-2^31 <= a,b,c <= 2^31-1`;
- произведение трёх 32-bit чисел может не поместиться в 64 бита;
- нужен многоразрядный результат.

## Решение

Храним модуль результата как unsigned 96-bit число:

```text
hi:mid:lo
```

Знак считаем отдельно:

```text
negative = sign(a) xor sign(b) xor sign(c)
```

Дальше работаем с модулями `abs(a)`, `abs(b)`, `abs(c)`.

## Умножение

Сначала:

```text
abs(a) * abs(b) -> 64-bit abHi:abLo
```

Потом умножаем 64-bit число на 32-bit:

```text
(abHi * 2^32 + abLo) * c
= abLo*c + (abHi*c << 32)
```

Схема:

```text
p0 = abLo * c     ; 64-bit
p1 = abHi * c     ; 64-bit

lo  = low32(p0)
mid = high32(p0) + low32(p1)
hi  = high32(p1) + carry
```

## Печать decimal

Чтобы вывести 96-bit число, делим его на 10 многоразрядно.

Один шаг деления:

```text
remainder = 0
for word in [hi, mid, lo]:
    cur = remainder:word
    quotientWord = cur / 10
    remainder = cur % 10
```

Полученный `remainder` — следующая десятичная цифра с конца.

Повторяем, пока `hi:mid:lo != 0`.

## Алгоритм

```text
read a,b,c
if any value is zero:
    print 0

sign = xor of signs
A = abs(a), B = abs(b), C = abs(c)
P = A * B * C as 96-bit

while P != 0:
    digit = P % 10
    push/store digit
    P = P / 10

if sign:
    print '-'
print digits in reverse order
```

## NASM-shape

Unsigned `mul`:

```asm
mov eax, [A]
mul dword [B]
; edx:eax = A * B
```

96-bit value in memory:

```asm
result_lo  resd 1
result_mid resd 1
result_hi  resd 1
```

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| хранить результат только в `edx:eax` | тройное произведение может быть больше 64 бит |
| печатать через `%lld` | может не хватить 64 бит |
| брать `abs(INT_MIN)` как signed positive | `2^31` не помещается в signed 32-bit, работай как unsigned magnitude |
| забыть особый случай нуля | нельзя печатать пустую строку цифр |
| неверно переносить carry при 64x32 | middle overflow должен уйти в high |

## Где в курсе

- [День 09 — деление](/day_09)
- [Big integer](/patterns/bigint)
- [Сложные задачи](/tasks/hard)
