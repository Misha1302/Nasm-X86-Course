# День 12. `cmp`, `test` и условные переходы

## Опора на материалы ВШЭ

`Slides2026-06.pdf`: `CMP`, `TEST`, таблица `Jcc`, signed/unsigned comparisons.

## Зачем этот день

`cmp` называется compare, но внутри это вычитание. Если это понять, условные переходы перестают быть магией.

## Главная мысль

`cmp a,b` выставляет флаги как после `a-b`, но результат не сохраняет. `test a,b` выставляет флаги как после `a&b`, но результат не сохраняет.

```text
cmp eax, ebx

temp = eax - ebx
temp is not stored
flags are updated

if temp == 0 -> ZF = 1
```

## Основные переходы

| Переход | Смысл |
|---|---|
| `je` | equal / zero |
| `jne` | not equal / not zero |
| `jg`, `jge` | signed `>`, `>=` |
| `jl`, `jle` | signed `<`, `<=` |
| `ja`, `jae` | unsigned `>`, `>=` |
| `jb`, `jbe` | unsigned `<`, `<=` |

## Пример

```asm
cmp eax, ebx
jg .greater_signed
ja .greater_unsigned

test eax, eax
je .zero
```

## Почему `jg` и `ja` не одно и то же

Одни и те же биты:

```text
0xFFFFFFFF
```

как unsigned: `4294967295`; как signed: `-1`.

Если:

```text
eax = 0xFFFFFFFF
ebx = 1
```

то signed: `-1 < 1`, а unsigned: `4294967295 > 1`.

## Мини-челленджи

1. Что значит `cmp eax, ebx` + `je L`?
2. Для `eax=0xFFFFFFFF`, `ebx=1`: какой переход сработает, `jg` или `ja`?
3. Напиши проверку `x == 0` через `test`.

<details>
<summary>Ответы / подсказки</summary>

1. `if (eax == ebx) goto L;`.
2. `ja`, если сравниваем как unsigned. `jg` не сработает.
3. `test eax,eax`; `je .zero`.

</details>

---
