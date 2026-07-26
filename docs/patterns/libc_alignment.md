# Паттерн: libc и 16-byte stack alignment

## Когда нужен

Этот контракт нужен для **каждого** вызова функции, собранной современной GNU/Linux i386 toolchain, а не только для Spring-04. GCC по умолчанию поддерживает 16-байтовую preferred stack boundary; смешивание старого 4-byte кода с системной libc требует явного realignment.

## Инвариант call site

Непосредственно перед `call`:

```text
esp % 16 == 0
```

После возврата caller обязан восстановить `esp` точно к состоянию до подготовки padding и аргументов.

## Выровненное тело `main`

Для учебного `main`, который возвращается через `ret`, используем простой frame:

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

`ebp` сохраняет исходную вершину frame, поэтому эпилог восстанавливает return address независимо от того, сколько байт отбросил `and esp, -16`.

## Padding как формула

Если body начинается с `esp % 16 == 0`, то:

```text
padding = (16 - (argument_bytes % 16)) % 16
```

Padding кладётся **до** аргументов. После вызова caller убирает `padding + argument_bytes`.

| Аргументы | Bytes | Padding | Cleanup |
|---|---:|---:|---:|
| один 32-bit | 4 | 12 | 16 |
| два 32-bit | 8 | 8 | 16 |
| три 32-bit | 12 | 4 | 16 |
| четыре 32-bit | 16 | 0 | 16 |
| format pointer + `double` | 12 | 4 | 16 |

## Пример: `printf("%d\n", x)`

```asm
sub esp, 8
push dword [x]
push fmtOut
call printf
add esp, 16
```

Перед `call` были сняты `8 + 4 + 4 = 16` байт.

## Пример: `scanf("%d%d", &a, &b)`

```asm
sub esp, 4
push b
push a
push fmtIn
call scanf
add esp, 16
```

Здесь `4 + 12 = 16`. В `scanf` передаются адреса.

## Пример: `printf("%f", value)` через x87

```asm
sub esp, 12
fstp qword [esp]
push fmtFloat
call printf
add esp, 16
```

`[esp..esp+7]` содержит `double` до `push`; после `push fmtFloat` он непрерывно лежит по `[esp+4..esp+11]`, а padding остаётся выше всех аргументов.

## Общая функция и wrapper

Если текущий `esp % 16` неизвестен, не угадывай padding. Либо:

1. создай выровненный frame через `and esp, -16` и восстанови исходный `esp` через frame pointer;
2. вынеси libc-call в wrapper с явно доказанным entry/exit state.

## Частые ошибки

| Ошибка | Почему неверно |
|---|---|
| считать alignment «требованием конкретной задачи» | это часть interop с современной toolchain/libc |
| очистить только argument bytes | padding останется и изменит frame state |
| добавить padding после аргументов | изменится layout параметров callee |
| считать успешный локальный запуск доказательством | libc может случайно терпеть misalignment |
| передать `[x]` в `scanf` | callee получает значение вместо адреса |

## Проверка

На breakpoint перед каждым внешним `call`:

```gdb
p/x $esp
p $esp % 16
```

Ожидается `0`. После cleanup значение `esp` должно совпасть с состоянием до подготовки вызова.
