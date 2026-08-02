# Популярные шаблоны NASM IA-32

Эта страница — краткая шпаргалка. Она не вводит новые правила и не является отдельным владельцем ABI-контракта. Для расчёта padding и очистки используй [канонический шаблон выравнивания](/patterns/libc_alignment), для CDECL — [справочник CDECL](/c_abi).

## 1. Минимальный `main`

```asm
section .text
global main

main:
    xor eax, eax
    ret
```

## 2. Выровненный `main`

```asm
main:
    push ebp
    mov ebp, esp
    and esp, -16

    ; body: esp % 16 == 0

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret
```

## 3. `scanf("%d", &x)`

Из состояния `esp % 16 == 0`:

```asm
sub esp, 8
push x
push fmtIn
call scanf
add esp, 16
```

`scanf` получает адрес, поэтому используется `x`, а не `[x]`.

## 4. `printf("%d", x)`

```asm
sub esp, 8
push dword [x]
push fmtOut
call printf
add esp, 16
```

`printf` получает значение.

## 5. `printf("%f", value)` из x87

```asm
sub esp, 12
fstp qword [esp]
push fmtFloat
call printf
add esp, 16
```

## 6. Классический кадр функции

Пролог:

```asm
push ebp
mov ebp, esp
sub esp, N
```

Эпилог:

```asm
mov esp, ebp
pop ebp
ret
```

Карта:

```text
[ebp+16]  argument 3
[ebp+12]  argument 2
[ebp+8]   argument 1
[ebp+4]   return address
[ebp]     old ebp
[ebp-4]   local 1
```

## 7. Собственная функция `sum(a,b)`

```asm
sum:
    push ebp
    mov ebp, esp

    mov eax, [ebp+8]
    add eax, [ebp+12]

    mov esp, ebp
    pop ebp
    ret
```

Вызов из выровненного участка:

```asm
sub esp, 8
push dword [b]
push dword [a]
call sum
add esp, 16
```

## 8. Сохранение `ebx`, `esi`, `edi`

```asm
f:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi

    ; body

    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
```

## 9. Простой `if`

C++:

```cpp
if (x == 0)
    y = 1;
```

NASM:

```asm
mov eax, [x]
test eax, eax
jne .end
mov dword [y], 1
.end:
```

## 10. `if / else`

```asm
mov eax, [x]
cmp eax, [y]
jle .else

mov eax, [x]
sub eax, [y]
jmp .end

.else:
mov eax, [y]
sub eax, [x]

.end:
mov [result], eax
```

## 11. Цикл по массиву `int`

```asm
xor ecx, ecx
xor eax, eax

.loop:
    cmp ecx, [n]
    jae .end

    add eax, [a + 4*ecx]
    inc ecx
    jmp .loop

.end:
```

## 12. Знаковое деление

```asm
mov eax, [x]
cdq
idiv dword [y]
; eax = quotient
; edx = remainder
```

## 13. Беззнаковое деление

```asm
mov eax, [x]
xor edx, edx
div dword [y]
```

## 14. Слияние по маске

```asm
; result = (a & mask) | (b & ~mask)
mov eax, [a]
and eax, [mask]

mov edx, [mask]
not edx
and edx, [b]

or eax, edx
```

## 15. Маска знака `0/-1`

```asm
mov edx, eax
sar edx, 31
```

## 16. Адрес элемента массива

```asm
; edx = base, ecx = i
lea eax, [edx + 4*ecx]   ; &a[i]
mov eax, [edx + 4*ecx]   ; a[i]
```

## Как пользоваться страницей

1. Сначала выведи шаблон из модели главы.
2. Затем сравни со шпаргалкой.
3. Не копируй вызов функции, пока не доказано исходное состояние `esp`.
4. При изменении числа или размера аргументов заново вычисли padding и cleanup.
