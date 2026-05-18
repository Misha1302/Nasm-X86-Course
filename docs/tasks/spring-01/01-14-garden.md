# 01-14. Огород

## Коротко

Самая важная идея: сначала считаем два ответа — ночной и дневной, потом выбираем без `if`.

<details open>
<summary>Подробное решение</summary>

Даны:

```text
N, M — размеры поля
K    — свёклы с квадратного метра
D    — штук в коробке
X:Y  — время на границе
```

### 1. Сколько всего свёклы

```text
items = N * M * K
```

Ограничения безопасные для 32-bit:

```text
1000 * 1000 * 1000 = 10^9
```

### 2. Сколько коробок

Последняя коробка может быть неполной, значит нужно округление вверх:

```text
boxes = ceil(items / D)
```

Для неотрицательных чисел:

```text
ceil(items / D) = (items + D - 1) / D
```

NASM-shape:

```asm
mov eax, [items]
add eax, [D]
dec eax
xor edx, edx
div dword [D]
; eax = boxes
```

Если `items = 0`, формула тоже даёт `0`:

```text
(0 + D - 1) / D = 0
```

### 3. Ночной ответ

Ночью пропускают всё:

```text
nightAnswer = boxes
```

Условие ночи:

```text
0:00 <= time <= 5:59
```

Так как часы `X` от `0` до `23`, достаточно проверить:

```text
X < 6
```

Минуты `Y` на ответ не влияют.

### 4. Дневной ответ

Днём коробки нумеруют с нуля и задерживают номера, кратные трём:

```text
0, 3, 6, 9, ...
```

Среди `boxes` коробок номера идут от `0` до `boxes - 1`.

Количество задержанных:

```text
blocked = ceil(boxes / 3)
```

Примеры:

| boxes | номера | blocked |
|---:|---|---:|
| 0 | — | 0 |
| 1 | 0 | 1 |
| 2 | 0,1 | 1 |
| 3 | 0,1,2 | 1 |
| 4 | 0,1,2,3 | 2 |

Дневной ответ:

```text
dayAnswer = boxes - blocked
```

### 5. Как выбрать без перехода

Нужна маска:

```text
nightMask = FFFFFFFFh, если X < 6
nightMask = 00000000h, иначе
```

Так как `X` в диапазоне `0..23`, можно сделать через знак `X - 6`:

```asm
mov eax, [X]
sub eax, 6
sar eax, 31        ; eax = -1 если X < 6, иначе 0
```

Выбор:

```text
answer = (nightAnswer & nightMask) | (dayAnswer & ~nightMask)
```

</details>

## Полный low-level shape

```text
items = N * M * K
boxes = ceil(items / D)
blocked = ceil(boxes / 3)
day = boxes - blocked
night = boxes
mask = sign_mask(X - 6)
answer = select(night, day, mask)
```

## Где может сломаться

- забыть, что коробки нумеруются с нуля;
- написать `blocked = boxes / 3`, хотя нужно `ceil(boxes / 3)`;
- использовать минуты `Y` в условии ночи: они не нужны;
- получить маску `0/1` вместо `0/FFFFFFFFh`;
- потерять `boxes` после `div`: деление меняет `eax` и `edx`.

## Где в курсе

- День 09: деление;
- День 10: маски;
- [Branchless-маски](/patterns/branchless).
