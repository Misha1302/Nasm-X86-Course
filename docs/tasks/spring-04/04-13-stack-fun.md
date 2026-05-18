# 04-13. Веселье со стеком

## Условие

Нужно реализовать функцию:

```c
apply(int* array, size_t length, void (*fn)(...), int n, ...);
```

Она должна пройти по массиву и для каждого элемента вызвать `fn`.

В этой задаче нужно использовать её примерно так:

```c
apply(array, length, fprintf, 2, stdout, "%d\n");
```

То есть для каждого `array[i]` должен получиться вызов:

```c
fprintf(stdout, "%d\n", array[i]);
```

Запрещён `io.inc`. Перед libc calls нужен 16-byte alignment.

## Ввод

```text
N a1 a2 ... aN
```

## Вывод

Каждое число в исходном порядке, по одному на строку.

## Ограничения

- числа signed 32-bit;
- нужно сохранить входной массив в памяти;
- главное требование — корректно реализовать `apply`.

## Layout аргументов `apply`

Внутри `apply`:

```text
[ebp+8]   array
[ebp+12]  length
[ebp+16]  fn
[ebp+20]  n
[ebp+24]  first vararg
[ebp+28]  second vararg
...
```

Для нужного вызова:

```text
n = 2
vararg 0 = stdout
vararg 1 = "%d\n"
```

## Что должен делать `apply`

Для каждого элемента `array[i]` собрать на стеке аргументы для `fn`:

```text
arg1 = stdout
arg2 = "%d\n"
arg3 = array[i]
```

Так как `cdecl` кладёт аргументы справа налево, push-порядок:

```text
push array[i]
push "%d\n"
push stdout
call fn
add esp, 12
```

В общем случае для `n` varargs:

```text
push array[i]
for k = n-1 downto 0:
    push vararg[k]
call fn
add esp, 4 * (n + 1)
```

## Алгоритм apply

```text
for i = 0..length-1:
    elem = array[i]

    push elem
    for k = n-1 downto 0:
        push vararg[k]

    call fn
    clean stack
```

## NASM-shape

Вызов function pointer:

```asm
mov eax, [ebp+16]    ; fn
call eax
```

Адрес `vararg[k]`:

```text
[ebp + 24 + 4*k]
```

Адрес `array[i]`:

```text
[array + 4*i]
```

## Alignment

Так как `fn` может быть `fprintf`, перед `call fn` нужно соблюсти 16-byte alignment.

Практический путь для учебного решения:

1. перед dynamic call посчитать, сколько байт будет pushed;
2. добавить padding, чтобы `esp` перед `call` был выровнен;
3. после вызова убрать и аргументы, и padding.

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| push varargs в прямом порядке | `cdecl` требует справа налево |
| вызвать `fn` как метку | `fn` лежит в аргументе, нужен indirect call |
| потерять `i`, `array`, `n` после вызова | `eax/ecx/edx` caller-saved |
| очистить только `array[i]` | надо убрать `4*(n+1)` байт плюс padding |
| забыть alignment | условие явно требует выравнивание для libc calls |

## Где в курсе

- [День 17 — CDECL](/day_17)
- [libc и alignment](/patterns/libc_alignment)
- [Advanced stack](/patterns/advanced_stack)
- [Сложные задачи](/tasks/hard)
