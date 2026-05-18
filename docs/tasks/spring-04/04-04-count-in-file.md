# 04-4. Count integers in file

## Условие

Во входном файле `data.in` записаны unsigned 32-bit числа. Нужно посчитать их количество и вывести на стандартный поток.

Запрещён `io.inc`. При вызове библиотечных функций стек должен быть выровнен по 16 байт.

## Ввод

Файл:

```text
data.in
```

Внутри файла — от 0 до 100000 unsigned 32-bit чисел.

## Вывод

Одно число: сколько чисел было в файле.

## Ограничения

- чисел не больше 100000;
- каждое число помещается в unsigned 32-bit;
- нужно работать с файлом через libc.

## Решение

Используем:

```c
FILE* f = fopen("data.in", "r");
while (fscanf(f, "%u", &x) == 1) {
    count++;
}
fclose(f);
printf("%u\n", count);
```

## Данные

```asm
fileName db "data.in", 0
modeRead db "r", 0
fmtU     db "%u", 0
fmtOut   db "%u", 10, 0
```

В `.bss`:

```asm
x resd 1
```

## NASM-shape

Открытие:

```asm
push modeRead
push fileName
call fopen
add esp, 8
; eax = FILE*
```

Чтение:

```asm
push x
push fmtU
push filePointer
call fscanf
add esp, 12

cmp eax, 1
jne .end_read
```

Перед каждым libc call нужен alignment.

## Ошибки

| Ошибка | Почему плохо |
|---|---|
| читать со stdin | вход задан в файле `data.in` |
| считать до EOF через `feof` | проще и правильнее проверять `fscanf == 1` |
| не закрыть файл | плохая привычка, хотя часто не ломает задачу |
| забыть alignment | явное требование условия |

## Где в курсе

- [Строки и файлы](/patterns/strings_files)
- [libc и alignment](/patterns/libc_alignment)
