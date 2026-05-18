# 04-13. Веселье со стеком

## Коротко

Это advanced ABI-задача. Нужно реализовать `apply`: function pointer, varargs, динамическая раскладка аргументов на стеке и 16-byte alignment.

<details open>
<summary>Подробное решение</summary>

Сигнатура по смыслу:

```c
void apply(int* array, size_t length, void (*fn)(...), int n, ...);
```

Для каждого `array[i]` нужно вызвать:

```text
fn(vararg0, vararg1, ..., varargN-1, array[i])
```

В конкретной задаче:

```c
apply(array, length, fprintf, 2, stdout, "%d\n");
```

Значит каждый внутренний вызов должен быть:

```c
fprintf(stdout, "%d\n", array[i]);
```

### 1. Где лежат параметры `apply`

В cdecl-фрейме:

```text
[ebp+8]   array
[ebp+12]  length
[ebp+16]  fn
[ebp+20]  n
[ebp+24]  first vararg
[ebp+28]  second vararg
...
```

### 2. Что нужно сделать в цикле

Для каждого элемента массива:

```text
1. взять array[i]
2. положить на стек array[i]
3. положить varargs в обратном порядке
4. вызвать fn
5. очистить стек
6. перейти к следующему i
```

Почему обратный порядок?

cdecl кладёт аргументы справа налево.

Для:

```c
fprintf(stdout, "%d\n", x);
```

push-порядок:

```asm
push x
push fmt
push stdout
call fprintf
add esp, 12
```

### 3. Общий push-loop для varargs

Если `n` varargs начинаются с `[ebp+24]`, последний vararg лежит по адресу:

```text
ebp + 24 + 4*(n-1)
```

Псевдо-NASM:

```asm
; сначала последний аргумент fn: array[i]
push dword [currentValue]

; потом varargs справа налево
mov ecx, [ebp+20]        ; n
.vararg_loop:
    test ecx, ecx
    jz .args_ready

    dec ecx
    push dword [ebp + 24 + ecx * 4]
    jmp .vararg_loop

.args_ready:
    call dword [ebp+16]
```

После вызова нужно очистить:

```text
4 * (n + 1) байт
```

### 4. Не храни важное в `eax/ecx/edx` через вызов `fn`

`fn` — обычная cdecl-функция. Она может испортить:

```text
eax, ecx, edx
```

Поэтому состояние цикла лучше держать:

- в локальных переменных;
- или в `ebx/esi/edi`, но тогда `apply` обязана сохранить и восстановить их.

Минимальный каркас:

```asm
apply:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    sub esp, 16       ; locals

    ; esi = array
    ; edi = i
    ; ebx = length

.done:
    add esp, 16
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
```

### 5. 16-byte alignment

В Spring-04 требуется выравнивать стек при библиотечных вызовах.

Если перед `call fn` нужно, чтобы `esp % 16 == 0`, то перед push-аргументами можно вычислить padding.

Идея:

```text
argBytes = 4 * (n + 1)
pad = (esp - argBytes) & 15
sub esp, pad
push args
call fn
add esp, argBytes
add esp, pad
```

NASM-shape:

```asm
mov eax, [n]
inc eax
shl eax, 2           ; eax = argBytes
mov [argBytes], eax

mov edx, esp
sub edx, eax
and edx, 15          ; edx = pad
mov [pad], edx
sub esp, edx

; push array[i]
; push varargs
; call fn

add esp, [argBytes]
add esp, [pad]
```

Это сложная часть задачи. Её лучше вынести в аккуратный helper/шаблон и не смешивать с логикой чтения массива.

</details>

## Где может сломаться

- вызвать `fn` с аргументами в прямом порядке;
- очистить только varargs, забыв `array[i]`;
- хранить индекс в `ecx` и потерять его после `fprintf`;
- не сохранить `ebx/esi/edi` внутри `apply`;
- забыть 16-byte alignment;
- перепутать `n` и `n+1`: `fn` получает `n` старых аргументов плюс текущий элемент.

## Где в курсе

- День 17: CDECL;
- [libc и alignment](/patterns/libc_alignment);
- [Advanced stack](/patterns/advanced_stack).
