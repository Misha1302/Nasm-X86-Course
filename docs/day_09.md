# День 09. Почему деление в x86 такое странное

## Опора на материалы ВШЭ

`Slides2026-04.pdf`, `Slides2026-06.pdf`: `mul/imul`, `div/idiv`, `edx:eax`, `cdq`.

## Зачем этот день

В C++ ты пишешь `x / y`. В x86 деление выглядит как ритуал. Нужно привыкнуть к схеме, и тогда деление перестанет быть страшным.

## Главная мысль

Для 32-битного деления делимое лежит в `edx:eax`, частное попадает в `eax`, остаток — в `edx`.

```text
+----------------+----------------+
|      edx       |      eax       |
+----------------+----------------+
   high              low

idiv ecx

eax = quotient
edx = remainder
```

## Signed и unsigned

| Operation | Unsigned | Signed |
|---|---|---|
| multiply | `mul` | `imul` |
| divide | `div` | `idiv` |
| prepare dividend | `xor edx, edx` | `cdq` |
| quotient | `eax` | `eax` |
| remainder | `edx` | `edx` |

## Signed division

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = x / y
; edx = x % y
```

## Unsigned division

```asm
mov eax, [x]
xor edx, edx
div dword [y]
; eax = x / y
; edx = x % y
```

## Почему нельзя `idiv eax, ecx`

В x86 у `idiv` делимое уже задано неявно: это `edx:eax`. Операнд у команды — только делитель.

Плохо:

```asm
idiv eax, ecx   ; такой формы нет
```

Хорошо:

```asm
mov eax, [x]
cdq
idiv ecx
```

## Мини-челленджи

1. Напиши фрагмент для signed `a / b`.
2. Напиши фрагмент для unsigned `a % b`.
3. Где лежит остаток после `idiv`?
4. Что может сломаться без `cdq`?

<details>
<summary>Ответы / подсказки</summary>

1. `mov eax,[a]`; `cdq`; `idiv dword [b]`.
2. `mov eax,[a]`; `xor edx,edx`; `div dword [b]`; результат остатка в `edx`.
3. В `edx`.
4. Делимое `edx:eax` будет неправильным.

</details>

---
