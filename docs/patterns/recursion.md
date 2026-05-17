# Паттерн: рекурсия в NASM

## Когда нужен

Когда условие требует рекурсивную функцию или запрещает массивы, но нужно “запомнить” хвост входа через стек вызовов.

## За 30 секунд

Рекурсия — это обычный `call`, только функция вызывает сама себя.

Главная опасность: после recursive call регистры caller-saved могут быть испорчены, а локальные значения надо хранить во фрейме или callee-saved регистрах.

## Карта фрейма

```text
[ebp+12]  argument 2
[ebp+8]   argument 1
[ebp+4]   return address
[ebp]     old ebp
[ebp-4]   local saved value
```

## Шаблон

```asm
func:
    push ebp
    mov ebp, esp
    sub esp, 4

    ; base case
    ; if (...) goto .base

    ; save value needed after recursion
    mov eax, [ebp+8]
    mov [ebp-4], eax

    ; recursive call
    push ...
    call func
    add esp, 4

    ; use saved value
    mov eax, [ebp-4]

.base:
    mov esp, ebp
    pop ebp
    ret
```

## Печать до/после рекурсии

```text
print before call  -> прямой порядок
print after call   -> обратный порядок
```

## Частые ошибки

| Ошибка | Почему плохо |
|---|---|
| нет базового случая | бесконечная рекурсия |
| значение осталось только в `eax` | recursive call может его испортить |
| забыть `add esp, ...` после call | стек уедет |
| использовать `ebx/esi/edi` без сохранения | нарушение CDECL |

## Закрывает задачи

- 03-4 Разворот половины последовательности.
