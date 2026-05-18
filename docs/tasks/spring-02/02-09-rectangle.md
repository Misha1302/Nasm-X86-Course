# 02-9. Прямоугольник

## Условие

Даны 4 вершины прямоугольника в произвольном порядке и точка `P`.

Стороны прямоугольника параллельны осям.

Нужно вывести `YES`, если точка строго внутри прямоугольника, иначе `NO`.

## Ввод

```text
x1 y1
x2 y2
x3 y3
x4 y4
px py
```

## Вывод

```text
YES
```

или:

```text
NO
```

## Ограничения

- координаты целые;
- `|coordinate| <= 1000`;
- вершины даны в произвольном порядке.

## Решение

Так как стороны параллельны осям, прямоугольник полностью задаётся границами:

```text
minX, maxX, minY, maxY
```

Точка строго внутри, если:

```text
minX < px < maxX
minY < py < maxY
```

## Алгоритм

```text
read first vertex
minX = maxX = x
minY = maxY = y

read other 3 vertices
update minX/maxX/minY/maxY

read px, py

if px > minX && px < maxX && py > minY && py < maxY:
    print YES
else:
    print NO
```

## NASM-shape

Обновление минимума:

```asm
mov eax, [x]
cmp eax, [minX]
jge .no_min_update
mov [minX], eax
.no_min_update:
```

Проверка строгой внутренности:

```asm
mov eax, [px]
cmp eax, [minX]
jle .no
cmp eax, [maxX]
jge .no

mov eax, [py]
cmp eax, [minY]
jle .no
cmp eax, [maxY]
jge .no

; yes
```

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| считать, что вершины идут по порядку | в условии произвольный порядок |
| использовать `<=` как внутри | точка на границе должна дать `NO` |
| сравнивать unsigned | координаты могут быть отрицательными |
| забыть `0` в строках `YES/NO` для `printf("%s")` | C-строки должны быть null-terminated |

## Где в курсе

- [День 12 — cmp/test/jcc](/day_12)
- [День 13 — if и циклы](/day_13)
