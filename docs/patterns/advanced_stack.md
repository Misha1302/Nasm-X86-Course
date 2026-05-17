# Advanced: function pointer и varargs

::: warning
Это advanced-паттерн. Не проходи его до CDECL, фреймов, массивов и alignment.
:::

## Когда нужен

Когда функция получает:

- указатель на функцию;
- переменное число аргументов;
- задачу “собрать вызов” вручную на стеке.

Пример C-shape:

```c
apply(array, length, fprintf, 2, stdout, "%d\n");
```

Здесь `fprintf` — function pointer, а `stdout, "%d\n"` — varargs, которые надо передать дальше.

## Что такое function pointer на уровне NASM

Указатель на функцию — это адрес кода.

Обычный вызов:

```asm
call fprintf
```

Вызов по указателю:

```asm
call eax        ; eax contains function address
```

Если адрес функции лежит в `[ebp+16]`, то:

```asm
mov eax, [ebp+16]
call eax
```

## CDECL layout для `apply`

Сигнатура:

```c
apply(int* array, size_t length, void (*fn)(...), int n, ...)
```

Frame:

```text
[ebp+8]   array
[ebp+12]  length
[ebp+16]  fn
[ebp+20]  n
[ebp+24]  vararg 0
[ebp+28]  vararg 1
...
```

Если `n = 2`, то varargs:

```text
[ebp+24] = stdout
[ebp+28] = "%d\n"
```

## Что должен делать `apply`

Для каждого элемента массива:

```c
fn(vararg0, vararg1, ..., varargNminus1, array[i]);
```

Для примера с `fprintf`:

```c
fprintf(stdout, "%d\n", array[i]);
```

## Как строить стек для `fn`

CDECL кладёт аргументы справа налево.

Для:

```c
fprintf(stdout, "%d\n", x);
```

нужно:

```asm
push x
push fmt
push stdout
call fprintf
add esp, 12
```

В общем случае:

1. сначала `push array[i]`;
2. потом push varargs в обратном порядке: `vararg[n-1] ... vararg[0]`;
3. вызвать `fn`;
4. убрать `(n + 1) * 4` байт аргументов.

## Почему varargs нельзя “просто передать”

`apply` не знает заранее, сколько дополнительных аргументов будет. Число лежит в `n`.

Значит нужен цикл:

```text
for j = n-1 downto 0:
    push vararg[j]
```

Адрес `vararg[j]`:

```text
[ebp + 24 + 4*j]
```

## Что сохранить

Внутри `apply` удобно держать:

```text
array pointer
length
i
fn pointer
n
```

Но после вызова `fn` регистры `eax/ecx/edx` могут быть испорчены. Поэтому важные значения держи:

- в локальных переменных;
- или в `ebx/esi/edi`, но сохрани их в начале функции и восстанови в конце.

## Alignment

Если `fn` — библиотечная функция, перед `call fn` тоже нужен 16-byte alignment.

Это делает задачу сложнее: ты строишь динамический список аргументов и одновременно следишь за стеком.

Безопасный подход:

```text
для каждого вызова fn:
    запомнить esp
    добавить padding
    push аргументы
    call fn
    восстановить esp
```

## Частые ошибки

| Ошибка | Почему плохо |
|---|---|
| вызвать `fn` как обычную метку | адрес функции приходит параметром |
| push varargs в прямом порядке | функция прочитает аргументы наоборот |
| забыть `array[i]` как последний аргумент | `fprintf` не получит число |
| не очистить `(n+1)*4` байт | стек уедет |
| хранить `i` в `ecx` через вызов `fn` | `fn` может испортить `ecx` |
| забыть alignment | Spring-04 может падать |

## Мини-практика

Для `n = 2` и varargs:

```text
stdout, fmt
```

какой порядок push для `fn(stdout, fmt, x)`?

Ответ:

```text
push x
push fmt
push stdout
call fn
```

## Закрывает задачи

- 04-13 Веселье со стеком.
