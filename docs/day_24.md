# День 24. C++-объект как struct с секретным указателем

## Опора на материалы ВШЭ

`Slides2026-0xD.pdf`: объект как структура, `vptr`, VMT, RTTI, virtual methods, `thiscall`.

## Зачем этот день

C++-объект выглядит высокоуровнево: поля, методы, virtual, наследование. Но в памяти это всё равно блок байтов плюс служебные указатели.

## Главная мысль

Объект похож на struct. Виртуальный вызов идёт через `vptr` и таблицу виртуальных методов. `this` — скрытый параметр метода.

## Картинка

```text
Object:

+------------------+
| vptr             | ---> +---------------------+
+------------------+      | virtual method #0   |
| field1           |      +---------------------+
+------------------+      | virtual method #1   |
| field2           |      +---------------------+
+------------------+
```

## Что где

| C++ feature | Low-level idea |
|---|---|
| field | fixed offset in object |
| non-virtual method | function + hidden `this` |
| virtual method | function pointer from VMT |
| inheritance | extended object layout |
| RTTI | runtime type information |

## Упрощённая форма virtual call

```asm
mov eax, [obj]        ; load vptr, simplified
call dword [eax]      ; indirect call through table
```

В реальном коде может быть больше шагов: загрузка объекта, загрузка `vptr`, смещение до нужного метода, косвенный вызов.

## Hidden `this`

Когда ты пишешь:

```cpp
obj.method(123);
```

на низком уровне это похоже на:

```cpp
method(&obj, 123);
```

То есть объект передаётся в метод как скрытый параметр.

## Мини-челленджи

1. Нарисуй объект с `vptr` и двумя полями.
2. Чем virtual call отличается от прямого `call label`?
3. Что такое hidden `this`?
4. Почему в объекте не хранятся имена методов?

<details>
<summary>Ответы / подсказки</summary>

- Virtual call идёт через указатель на функцию из таблицы.
- Hidden `this` — адрес объекта, передаваемый методу.
- Имена методов нужны компилятору/линкеру/отладке, но не обычному layout объекта.

</details>

---
