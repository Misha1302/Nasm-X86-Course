# 03-18. Знаковое произведение

## Коротко

Произведение трёх signed 32-bit чисел в общем случае не помещается в 64 бита. Нужна многоразрядная арифметика: минимум 96 бит.

<details open>
<summary>Подробное решение</summary>

Вход:

```text
a, b, c: signed int32
```

Худший порядок величины:

```text
2^31 * 2^31 * 2^31 = 2^93
```

Значит, одного `edx:eax` мало. Храним модуль результата в трёх `dword`:

```text
hi:mid:lo    ; 96-bit unsigned
```

### 1. Определить знак

Знак результата отрицательный, если отрицательных множителей нечётное число.

C-shape:

```cpp
neg = (a < 0) ^ (b < 0) ^ (c < 0);
```

В NASM можно проверять каждый множитель через `cmp`/`jge` или через sign bit.

### 2. Взять модули множителей

Для каждого signed 32-bit числа получить unsigned-модуль.

Branchless abs-shape:

```asm
; eax = signed value
mov edx, eax
sar edx, 31
xor eax, edx
sub eax, edx
; eax = abs(value) as unsigned bits
```

Это корректно даже для `INT_MIN`: получится `0x80000000`, то есть unsigned-модуль `2147483648`.

### 3. Умножить первые два числа

Unsigned `mul` даёт 64-bit результат:

```asm
mov eax, [absA]
mul dword [absB]
; edx:eax = absA * absB
```

Сохраняем:

```text
pLo = eax
pHi = edx
```

### 4. Умножить 64-bit число на третий 32-bit множитель

Нужно:

```text
(pHi:pLo) * absC
```

Раскладываем:

```text
pLo * absC -> low part + carry
pHi * absC -> middle/high part
```

NASM-shape:

```asm
; pLo, pHi, absC лежат в памяти

mov eax, [pLo]
mul dword [absC]
mov [res0], eax      ; lo
mov [carry0], edx

mov eax, [pHi]
mul dword [absC]
; edx:eax = pHi * absC

add eax, [carry0]
adc edx, 0

mov [res1], eax      ; mid
mov [res2], edx      ; hi
```

Теперь:

```text
res2:res1:res0 = abs(a*b*c)
```

### 5. Напечатать 96-bit число в decimal

Повторяем деление большого числа на `10`.

Делим по словам сверху вниз:

```text
remainder = 0
(q2, remainder) = div(remainder:res2, 10)
(q1, remainder) = div(remainder:res1, 10)
(q0, remainder) = div(remainder:res0, 10)
```

NASM-shape одного шага:

```asm
mov ecx, 10
xor edx, edx

mov eax, [res2]
div ecx
mov [res2], eax      ; q2, edx = rem

mov eax, [res1]
div ecx
mov [res1], eax      ; q1, edx = rem

mov eax, [res0]
div ecx
mov [res0], eax      ; q0, edx = digit
```

`edx` после последнего `div` — очередная десятичная цифра от конца.

Сохраняем цифры в буфер, потом печатаем в обратном порядке.

### 6. Ноль

Если результат равен нулю, печатаем просто:

```text
0
```

Минус печатаем только если результат не ноль и `neg = 1`.

</details>

## Где может сломаться

- использовать только 64-bit результат;
- сломать `INT_MIN` при обычном `neg`;
- забыть перенос `adc edx, 0` при умножении `pHi * absC`;
- печатать `hi:mid:lo` как hex, а нужен decimal;
- при делении 96-bit на 10 идти снизу вверх, а надо сверху вниз.

## Где в курсе

- День 09: `mul`, `div`;
- День 10: branchless abs;
- [Big integer](/patterns/bigint).
