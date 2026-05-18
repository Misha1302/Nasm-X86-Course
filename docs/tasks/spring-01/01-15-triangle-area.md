# 01-15. Площадь треугольника

## Коротко

Float не нужен. Считай удвоенную площадь, потом печатай `.0` или `.5`.

<details open>
<summary>Подробное решение</summary>

Даны три точки:

```text
(x1, y1), (x2, y2), (x3, y3)
```

Удвоенная ориентированная площадь:

```text
det = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
```

Настоящая площадь:

```text
area = abs(det) / 2
```

### 1. Считаем determinant

C++-shape:

```cpp
int dx21 = x2 - x1;
int dy31 = y3 - y1;
int dx31 = x3 - x1;
int dy21 = y2 - y1;

int det = dx21 * dy31 - dx31 * dy21;
```

NASM-shape:

```asm
mov eax, [x2]
sub eax, [x1]

mov ecx, [y3]
sub ecx, [y1]
imul eax, ecx        ; part1

mov edx, [x3]
sub edx, [x1]

mov ecx, [y2]
sub ecx, [y1]
imul edx, ecx        ; part2

sub eax, edx         ; det
```

Координаты до `10000`, произведения безопасны для 32-bit.

### 2. Берём `abs(det)` без переходов

```asm
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
; eax = abs(det)
```

### 3. Делим на 2

```asm
xor edx, edx
mov ecx, 2
div ecx
; eax = integer part
; edx = remainder: 0 или 1
```

Дробная часть:

```text
remainder = 0 -> .0
remainder = 1 -> .5
```

Можно напечатать двумя числами:

```c
printf("%u.%u\n", integerPart, remainder * 5);
```

</details>

## Ручной тест

Точки:

```text
(1,1), (0,1), (1,0)
```

```text
det = (0-1)*(0-1) - (1-1)*(1-1) = 1
area = 1/2 = 0.5
```

## Где может сломаться

- забыть `abs(det)`;
- пытаться использовать x87, хотя задача проще через целые числа;
- вывести `0.1` вместо `0.5`, если печатать остаток напрямую;
- использовать `%d` для `integerPart`, хотя после `abs` удобнее unsigned.

## Где в курсе

- День 07: арифметика;
- День 09: деление;
- День 10: branchless `abs`.
