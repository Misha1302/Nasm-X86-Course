# 04-7. Различные строки

## Условие

Дано количество строк, затем сами строки. Нужно вывести количество различных строк.

Строки разделены пробелами или переводами строк.

Запрещён `io.inc`. При вызове библиотечных функций стек должен быть выровнен по 16 байт.

## Ввод

```text
N
s1 s2 ... sN
```

## Вывод

Одно число: количество различных строк.

## Ограничения

- `0 <= N <= 500`;
- длина строки не больше 10;
- строки удобно хранить в фиксированных слотах.

## Решение

Храним только уже найденные различные строки.

Для каждой новой строки:

1. сравниваем её со всеми сохранёнными через `strcmp`;
2. если совпадение найдено — не добавляем;
3. если совпадения нет — копируем строку в следующий слот и увеличиваем `distinctCount`.

## Память

Длина строки `<= 10`, но нужен `0`-terminator. Можно взять слот 16 байт:

```asm
section .bss
    current resb 16
    strings resb 500 * 16
```

Адрес `strings[i]`:

```text
strings + i * 16
```

## Алгоритм

```text
read N
distinct = 0

for i = 0..N-1:
    read current
    found = false

    for j = 0..distinct-1:
        if strcmp(current, strings[j]) == 0:
            found = true
            break

    if not found:
        strcpy(strings[distinct], current)
        distinct++

print distinct
```

## NASM-shape

`strcmp(current, saved)`:

```asm
push savedAddress
push current
call strcmp
add esp, 8

test eax, eax
je .found
```

`strcpy(destination, source)`:

```asm
push current
push destination
call strcpy
add esp, 8
```

Перед каждым libc call нужен alignment.

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| сравнивать адреса строк | нужно сравнивать содержимое через `strcmp` |
| выделить 10 байт на строку | нужен байт `0` |
| не ограничить `%s` | лучше читать через `%15s` |
| перепутать аргументы `strcpy` | сначала destination, потом source |
| забыть alignment | явное требование условия |

## Где в курсе

- [Строки и файлы](/patterns/strings_files)
- [libc и alignment](/patterns/libc_alignment)
