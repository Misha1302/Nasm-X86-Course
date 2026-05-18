# 01-15. Площадь треугольника

## Условие

Даны координаты трёх вершин треугольника. Нужно вывести площадь с точностью до одного знака после запятой.

Запрещены условные передачи и условное управление.

## Ввод

```text
x1 y1
x2 y2
x3 y3
```

## Вывод

Площадь в формате:

```text
целая_часть.дробная_часть
```

Например:

```text
0.5
```

## Ограничения

- все координаты целые;
- `|coordinate| <= 10000`;
- determinant помещается в signed 32-bit.

## Решение

Площадь треугольника:

```text
S = abs(det) / 2
```

где:

```text
det = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
```

Так как координаты целые, `abs(det) / 2` всегда имеет дробную часть только `.0` или `.5`.

Значит floating point не нужен.

```text
whole = abs(det) / 2
frac  = (abs(det) % 2) * 5
```

## Branchless abs

```asm
; eax = det
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
; eax = abs(det)
```

## NASM-shape

```asm
; part1 = (x2 - x1) * (y3 - y1)
mov eax, [x2]
sub eax, [x1]
mov ecx, [y3]
sub ecx, [y1]
imul eax, ecx
mov esi, eax

; part2 = (x3 - x1) * (y2 - y1)
mov eax, [x3]
sub eax, [x1]
mov ecx, [y2]
sub ecx, [y1]
imul eax, ecx

; det = part1 - part2
mov ecx, esi
sub ecx, eax
```

Потом берём `abs(ecx)` и делим на 2.

## Вывод

```asm
; whole = absDet / 2
; frac = (absDet & 1) * 5
```

Формат:

```asm
fmtOut db "%d.%d", 10, 0
```

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| использовать `if (det < 0)` | переходы запрещены |
| печатать через `%f` | floating point не нужен |
| забыть `abs(det)` | площадь не может быть отрицательной |
| округлять вещественное число | точный ответ всегда `.0` или `.5` |

## Где в курсе

- [День 07 — арифметика](/day_07)
- [День 10 — branchless-домашка](/day_10)
- [Branchless-маски](/patterns/branchless)
