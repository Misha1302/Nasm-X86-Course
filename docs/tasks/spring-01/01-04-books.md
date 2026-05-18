# 01-4. Книжки

## Коротко

Это чистая формула. Условные переходы не нужны.

<details open>
<summary>Подробное решение</summary>

К началу 2011 года есть `X` книг.

За один год изменение:

```text
delta = N - M
```

К началу года `Y` прошло:

```text
years = Y - 2011
```

Ответ:

```text
answer = X + years * delta
```

C++-shape:

```cpp
int years = Y - 2011;
int delta = N - M;
int answer = X + years * delta;
```

NASM-shape:

```asm
mov eax, [Y]
sub eax, 2011        ; years

mov ecx, [N]
sub ecx, [M]         ; delta

imul eax, ecx        ; years * delta
add eax, [X]
```

</details>

## Ручные тесты

| Вход | Проверка |
|---|---|
| `123 23 42 2012` | `123 + 1 * (23 - 42) = 104` |
| `10 3 4 2013` | `10 + 2 * (3 - 4) = 8` |

## Где может сломаться

- взять `Y - 2010` вместо `Y - 2011`;
- перепутать `N - M` и `M - N`;
- искать несуществующий `if`, хотя задача полностью линейная.

## Где в курсе

- День 07: арифметика;
- День 10: branchless-задачи Spring-01.
