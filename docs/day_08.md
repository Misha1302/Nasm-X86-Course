# День 08. Как один байт становится `255` или `-1`

## Опора на материалы ВШЭ

`Slides2026-03.pdf`, `Slides2026-04.pdf`: `movsx`, `movzx`, `cbw/cwd/cdq`, подготовка к `idiv`.

## Зачем этот день

`0xFF` — это просто восемь единиц. Но C++ может видеть здесь `255` или `-1`. В ассемблере ты сам выбираешь, как расширить маленькое значение до большого.

## Главная мысль

`movzx` добавляет нули. `movsx` копирует знаковый бит. `cdq` копирует знак `eax` в `edx` перед `idiv`.

## Картинка

```text
x = 0xFF = 11111111

movzx -> 00000000 00000000 00000000 11111111 = 255
movsx -> 11111111 11111111 11111111 11111111 = -1
```

## Пример

```asm
movsx eax, byte [signedChar]
movzx edx, word [unsignedShort]

mov eax, [x]
cdq
idiv dword [y]
```

## Таблица

| Instruction | Что делает |
|---|---|
| `movzx` | zero extension |
| `movsx` | sign extension |
| `cbw` | `AL -> AX`, sign extension |
| `cwd` | `AX -> DX:AX`, sign extension |
| `cdq` | `EAX -> EDX:EAX`, sign extension |

## Почему `cdq` нужен перед `idiv`

`idiv` делит не просто `eax`, а пару `edx:eax`. Для signed division старшая половина должна быть правильным знаковым расширением.

```asm
mov eax, -7
cdq          ; edx станет FFFFFFFFh
idiv ecx
```

Если забыть `cdq`, в `edx` может лежать мусор от старых вычислений.

## Мини-челленджи

1. Что даст `movzx` для байта `0x80`?
2. Что даст `movsx` для байта `0x80`?
3. Что делает `cdq`, если `eax` положительный?
4. Что делает `cdq`, если `eax` отрицательный?

<details>
<summary>Ответы / подсказки</summary>

1. `0x00000080` = 128.
2. `0xFFFFFF80` = -128.
3. `edx = 0`.
4. `edx = 0xFFFFFFFF`.

</details>

---
