# День 13. `if`, циклы и GOTO-форма

## Опора на материалы ВШЭ

`Slides2026-06.pdf`: GOTO-форма, `if/else`, циклы, popcount.

## Зачем этот день

В asm нет `if` и `while`. Есть метки и переходы. Это не хуже — просто честнее.

## Главная мысль

Управляющие конструкции C/C++ раскладываются в `cmp/test`, `jcc`, `jmp` и метки.

## `if/else`

C++:

```cpp
if (x > y) {
    result = x - y;
} else {
    result = y - x;
}
```

Форма в asm:

```asm
cmp x, y
jle .else
.then:
    ; result = x - y
    jmp .end
.else:
    ; result = y - x
.end:
```

Главный трюк: после then-ветки нужен `jmp .end`, иначе выполнение “провалится” в else.

## Цикл `while`

```cpp
while (x != 0) {
    x >>= 1;
}
```

```asm
.loop:
    test eax, eax
    je .end
    shr eax, 1
    jmp .loop
.end:
```

## Popcount-пример

```asm
xor ecx, ecx
.loop:
    test edx, edx
    je .end
    mov eax, edx
    and eax, 1
    add ecx, eax
    shr edx, 1
    jmp .loop
.end:
```

Здесь `edx` — число, `ecx` — счётчик единичных битов.

## Таблица

| C/C++ | Assembly shape |
|---|---|
| `if` | условный переход через тело |
| `if/else` | условный переход + `jmp end` |
| `while` | проверка перед телом |
| `do while` | проверка после тела |
| `break` | `jmp` на конец цикла |
| `continue` | `jmp` на проверку/следующую итерацию |

## Мини-челленджи

1. Перепиши `if (x==0) y=1; else y=2;` в GOTO-форму.
2. Напиши цикл `while (x>0) x--;`.
3. Объясни popcount-фрагмент выше.

<details>
<summary>Подсказки</summary>

Для `while (x>0)` можно использовать `cmp eax,0` и `jle .end`.

</details>

---
