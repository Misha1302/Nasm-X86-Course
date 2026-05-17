# Advanced: function pointer и varargs

::: warning
Это advanced-паттерн. Не проходи его до CDECL, фреймов, массивов и alignment.
:::

## Когда нужен

Когда функция получает указатель на функцию и переменное число аргументов.

Пример C-shape:

```c
apply(array, length, fprintf, 2, stdout, "%d\n");
```

## Что проверяется

- CDECL layout;
- function pointer call;
- varargs;
- ручное построение аргументов на стеке;
- сохранение регистров;
- 16-byte alignment.

## Stack-shape для `fprintf(stdout, "%d\n", x)`

Аргументы справа налево:

```text
push x
push fmt
push stdout
call fprintf
```

В задаче `apply` эти аргументы надо строить внутри цикла для каждого элемента массива.

## Частые ошибки

| Ошибка | Почему плохо |
|---|---|
| вызвать `fn` с неправильным порядком аргументов | функция прочитает мусор |
| не сохранить `array/length/fn/n` | они потеряются после call |
| не учитывать varargs | количество push зависит от `n` |
| забыть alignment | Spring-04 может падать |

## Закрывает задачи

- 04-13 Веселье со стеком.
