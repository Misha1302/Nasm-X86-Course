# x86 C ABI / CDECL: как вызывать C-функции из NASM

## Зачем эта страница

Да, без отдельной страницы про ABI курс получается неполным.

Ученик может знать `push`, `call`, `ret`, но всё равно не понимать:

- почему аргументы кладутся справа налево;
- почему после `printf` пишем `add esp, 8` или `add esp, 12`;
- почему `scanf` получает адрес, а `printf` значение;
- какие регистры функция имеет право испортить;
- где лежит return value;
- почему `[ebp+8]` — первый аргумент;
- почему variadic-функции вроде `printf` требуют аккуратности.

Эта страница — практическая шпаргалка по **32-bit x86 C ABI / CDECL** для Linux/NASM-задач курса.

---

## Главное за 30 секунд

Для обычного 32-bit x86 CDECL:

```text
arguments -> stack, right-to-left
return    -> eax
cleanup   -> caller cleans stack
scratch   -> eax, ecx, edx may be destroyed
preserved -> ebx, esi, edi, ebp should survive call
stack     -> grows downward
```

Мини-пример:

```c
printf("%d\n", x);
```

NASM:

```asm
push dword [x]      ; second argument: x
push fmtOut         ; first argument: "%d\n"
call printf
add esp, 8          ; caller removes 2 arguments * 4 bytes
```

---

# 1. Что такое ABI

ABI = Application Binary Interface.

Если очень просто, ABI — это договор между машинным кодом разных модулей.

Он отвечает на вопросы:

| Вопрос | ABI говорит |
|---|---|
| Где лежат аргументы функции? | В регистрах или на стеке |
| Кто очищает аргументы со стека? | Caller или callee |
| Где лежит возвращаемое значение? | Обычно в `eax` |
| Какие регистры можно портить? | Caller-saved |
| Какие регистры надо восстановить? | Callee-saved |
| Как выровнен стек? | По правилам платформы |
| Как называются символы и функции? | Правила линковки |

Без ABI `main.asm` не смог бы нормально вызвать `printf`, а C-код не смог бы вызвать твою NASM-функцию.

---

# 2. CDECL в IA-32

В этом курсе для Linux x86 мы используем практическую модель CDECL:

```text
cdecl = аргументы на стеке + caller clean-up + return in eax
```

CDECL важен, потому что `printf`, `scanf` и обычные C-функции в 32-bit учебной среде вызываются именно в этой логике.

---

# 3. Стек растёт вниз

Перед вызовами нужно помнить:

```text
push value:
    esp = esp - 4
    [esp] = value

pop reg:
    reg = [esp]
    esp = esp + 4
```

Картинка:

```text
higher addresses
+------------------+
| older data       |
+------------------+
| argument 2       |
+------------------+
| argument 1       | <- esp before call
+------------------+
lower addresses
```

---

# 4. Аргументы кладутся справа налево

C:

```c
f(a, b, c);
```

CDECL:

```asm
push c
push b
push a
call f
add esp, 12
```

Почему так?

После трёх `push` ближе всего к `esp` лежит первый аргумент `a`. Функции удобно читать его как первый аргумент.

```text
higher addresses
+------------------+
| c                | third argument
+------------------+
| b                | second argument
+------------------+
| a                | first argument  <- esp before call
+------------------+
lower addresses
```

После `call` процессор сам кладёт return address, поэтому внутри функции после пролога первый аргумент окажется по `[ebp+8]`.

---

# 5. `call` добавляет return address

Вызов:

```asm
call f
```

делает две вещи:

```text
1. push address_after_call
2. jump to f
```

Поэтому внутри функции на стеке есть return address.

Перед `call f` после аргументов:

```text
esp -> [ first argument ]
       [ second argument ]
```

Сразу после входа в `f`:

```text
esp -> [ return address ]
       [ first argument  ]
       [ second argument ]
```

---

# 6. Почему первый аргумент — `[ebp+8]`

Классический пролог функции:

```asm
push ebp
mov ebp, esp
```

После него стек выглядит так:

```text
higher addresses
+------------------+
| argument 2       | [ebp+12]
+------------------+
| argument 1       | [ebp+8]
+------------------+
| return address   | [ebp+4]
+------------------+
| old ebp          | [ebp]
+------------------+
lower addresses
```

Поэтому:

```text
[ebp]     = old ebp
[ebp+4]   = return address
[ebp+8]   = first argument
[ebp+12]  = second argument
[ebp+16]  = third argument
```

Это нужно выучить до автоматизма.

---

# 7. Caller clean-up

CDECL означает: **стек после вызова чистит вызывающий код**.

Если ты сделал:

```asm
push b
push a
call f
```

ты сам должен убрать аргументы:

```asm
add esp, 8
```

Общее правило:

```text
bytes_to_remove = argument_count * 4
```

Примеры:

| Вызов | После call |
|---|---|
| `f(a)` | `add esp, 4` |
| `f(a,b)` | `add esp, 8` |
| `f(a,b,c)` | `add esp, 12` |
| `printf("%d", x)` | `add esp, 8` |
| `scanf("%d%d", &a, &b)` | `add esp, 12` |

Если забыть `add esp, ...`, стек останется ниже, чем должен. Ошибка может проявиться не сразу, но это неправильный код.

---

# 8. Return value

Обычный `int` возвращается в `eax`.

C:

```c
int sum(int a, int b) {
    return a + b;
}
```

NASM:

```asm
sum:
    push ebp
    mov ebp, esp

    mov eax, [ebp+8]
    add eax, [ebp+12]

    pop ebp
    ret
```

После:

```asm
call sum
```

результат лежит в:

```text
eax
```

Для некоторых 64-битных integer-результатов может использоваться пара:

```text
edx:eax
```

Для floating point при старом x87-стиле результат может быть в `st(0)`. Но в базовых задачах чаще всего нужен `eax`.

---

# 9. Caller-saved и callee-saved

После вызова функции часть регистров может быть испорчена.

## Caller-saved

```text
eax, ecx, edx
```

Функция имеет право их менять.

Если вызывающему они нужны после `call`, он должен сохранить их сам.

```asm
push eax
push ecx
call f
pop ecx
pop eax
```

## Callee-saved

```text
ebx, esi, edi, ebp
```

Если функция использует эти регистры, она должна восстановить их перед `ret`.

```asm
my_func:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi

    ; use ebx, esi, edi

    pop edi
    pop esi
    pop ebx
    pop ebp
    ret
```

`esp` тоже должен быть восстановлен в корректное состояние. Иначе `ret` сломается.

---

# 10. Почему `printf` портит `eax`

После:

```asm
call printf
```

нельзя рассчитывать, что `eax`, `ecx`, `edx` сохранились.

Например, плохо:

```asm
mov eax, [answer]

push eax
push fmtOut
call printf
add esp, 8

; здесь eax уже может быть не answer
add eax, 1
```

Если значение нужно после `printf`, сохрани его:

```asm
mov eax, [answer]
push eax              ; save answer

push eax
push fmtOut
call printf
add esp, 8

pop eax               ; restore answer
add eax, 1
```

Но чаще проще не использовать `eax` после `printf`.

---

# 11. `printf`: значение, не адрес

C:

```c
printf("%d\n", x);
```

NASM:

```asm
push dword [x]
push fmtOut
call printf
add esp, 8
```

Почему `[x]`?

Потому что `printf` должен напечатать значение.

Если ответ уже в `eax`:

```asm
push eax
push fmtOut
call printf
add esp, 8
```

---

# 12. `scanf`: адрес, не значение

C:

```c
scanf("%d", &x);
```

NASM:

```asm
push x
push fmtIn
call scanf
add esp, 8
```

Почему `x`, а не `[x]`?

Потому что `scanf` должен записать число в переменную, значит ему нужен адрес.

Плохо:

```asm
push dword [x]
push fmtIn
call scanf
```

Так ты передаёшь старое значение `x` как будто это адрес. Это почти гарантированно ошибка.

---

# 13. `scanf("%d%d", &a, &b)`

C:

```c
scanf("%d%d", &a, &b);
```

Аргументы:

```text
1: format
2: &a
3: &b
```

Push справа налево:

```asm
push b
push a
push fmt2
call scanf
add esp, 12
```

Строка формата:

```asm
fmt2 db "%d%d", 0
```

---

# 14. `printf("%d %d\n", a, b)`

C:

```c
printf("%d %d\n", a, b);
```

Аргументы:

```text
1: format
2: a
3: b
```

Push справа налево:

```asm
push dword [b]
push dword [a]
push fmt2Out
call printf
add esp, 12
```

Строка:

```asm
fmt2Out db "%d %d", 10, 0
```

---

# 15. Variadic-функции: почему `printf` и `scanf` особенные

`printf` и `scanf` — variadic functions. Они принимают переменное количество аргументов.

```c
printf("%d", x);
printf("%d %d", a, b);
printf("%f", d);
```

Форматная строка говорит функции, сколько аргументов и какого типа ожидать.

Поэтому если формат и реальные аргументы не совпадают, будет мусор или падение.

Примеры ошибок:

```asm
; формат ждёт int, а аргумент не положили
push fmtOut
call printf
add esp, 4
```

```asm
; scanf ждёт адрес int, а передали значение int
push dword [x]
push fmtIn
call scanf
add esp, 8
```

```asm
; printf("%f") ждёт double 8 bytes, а дали float 4 bytes
fstp dword [esp]
```

---

# 16. Про `printf("%f")` и `qword`

В C variadic-функциях `float` продвигается до `double`.

Поэтому:

```c
printf("%f", value);
```

ждёт `double`, то есть 8 байт.

NASM-идея с x87:

```asm
sub esp, 8
fstp qword [esp]
push fmtFloat
call printf
add esp, 12
```

Почему `12`?

```text
8 bytes double + 4 bytes format pointer = 12 bytes
```

---

# 17. Stack alignment: коротко и честно

В простых учебных IA-32 задачах обычно достаточно держать стек **сбалансированным**: сколько положил через `push`, столько убрал через `add esp, ...` или `pop`.

Но в реальных ABI и с современными компиляторами может быть дополнительное требование к выравниванию стека, особенно вокруг SSE и библиотечных вызовов.

Практическое правило для курса:

1. Не порти `esp` без причины.
2. После каждого CDECL-вызова убирай аргументы.
3. Перед вызовом libc не оставляй стек в случайном состоянии.
4. Если пишешь сложную функцию с локальными данными и вызовами, следи за выравниванием отдельно.

Для наших базовых задач главная ошибка почти всегда не “идеальное 16-byte alignment”, а забытый `add esp, ...` или неправильный аргумент.

---

# 18. Полный пример: функция NASM вызывается из NASM

```asm
section .data
    fmtOut db "%d", 10, 0

section .text
    extern printf
    global main

sum:
    push ebp
    mov ebp, esp

    mov eax, [ebp+8]
    add eax, [ebp+12]

    pop ebp
    ret

main:
    push 7
    push 5
    call sum
    add esp, 8

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

Что печатает?

```text
12
```

Почему?

`sum(5,7)` возвращает `12` в `eax`, потом `printf` печатает `eax`.

---

# 19. Полный пример: `scanf`, вычисление, `printf`

```asm
section .data
    fmtIn db "%d%d", 0
    fmtOut db "%d", 10, 0

section .bss
    a resd 1
    b resd 1

section .text
    extern scanf
    extern printf
    global main

main:
    push b
    push a
    push fmtIn
    call scanf
    add esp, 12

    mov eax, [a]
    imul eax, [b]
    add eax, 10

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
```

C-смысл:

```c
scanf("%d%d", &a, &b);
printf("%d\n", a*b + 10);
```

---

# 20. Отличие CDECL от других calling conventions

В слайдах могут встречаться и другие соглашения вызова. Коротко:

| Convention | Идея |
|---|---|
| `cdecl` | аргументы на стеке, caller clean-up |
| `stdcall` | аргументы на стеке, callee clean-up |
| `fastcall` | часть аргументов через регистры |
| `thiscall` | C++ method call, hidden `this` часто через регистр |

В этом курсе для задач держим в голове именно:

```text
32-bit Linux/NASM + libc -> practical cdecl model
```

x64 ABI не мешаем сюда: там аргументы обычно идут через регистры и правила другие.

---

# 21. Мини-челленджи

### 1. Вызов `f(a,b,c)`

Напиши CDECL-push sequence.

<details>
<summary>Ответ</summary>

```asm
push c
push b
push a
call f
add esp, 12
```

</details>

### 2. Где первый аргумент внутри функции?

<details>
<summary>Ответ</summary>

`[ebp+8]`.

</details>

### 3. Почему после `printf("%d", x)` нужно `add esp, 8`?

<details>
<summary>Ответ</summary>

Было два аргумента по 4 байта: format pointer и `x`.

</details>

### 4. Какие регистры функция может испортить?

<details>
<summary>Ответ</summary>

Обычно `eax`, `ecx`, `edx` — caller-saved.

</details>

### 5. Какие регистры функция должна восстановить, если использует?

<details>
<summary>Ответ</summary>

Обычно `ebx`, `esi`, `edi`, `ebp` — callee-saved.

</details>

### 6. Что передать в `scanf("%d", &x)`?

<details>
<summary>Ответ</summary>

Адрес `x`:

```asm
push x
push fmtIn
call scanf
add esp, 8
```

</details>

### 7. Что передать в `printf("%d", x)`?

<details>
<summary>Ответ</summary>

Значение `[x]`:

```asm
push dword [x]
push fmtOut
call printf
add esp, 8
```

</details>

---

# 22. Типовые ошибки

| Ошибка | Почему плохо |
|---|---|
| передать `[x]` в `scanf` | нужен адрес, а не значение |
| передать `x` в `printf("%d")` | напечатаешь адрес, а не значение |
| забыть `add esp, ...` | caller не очистил аргументы |
| перепутать порядок push | функция прочитает аргументы не так |
| считать `[ebp+4]` первым аргументом | это return address |
| хранить важное значение в `eax` через `call printf` | `eax` caller-saved, функция может его испортить |
| использовать `ebx/esi/edi` в своей функции и не восстановить | нарушаешь ABI |
| передать `dword` для `%f` | `%f` ждёт `double`, 8 байт |

---

# 23. Что должно остаться в голове

После этой страницы ты должен уметь:

- объяснить, что такое ABI;
- вызвать C-функцию из NASM;
- правильно положить аргументы справа налево;
- очистить стек после CDECL-вызова;
- понять `[ebp+8]`, `[ebp+12]`;
- знать, что return value лежит в `eax`;
- не рассчитывать на сохранность `eax/ecx/edx` после вызова;
- сохранять `ebx/esi/edi`, если пишешь свою функцию и используешь их;
- корректно вызывать `scanf`, `printf`, `printf("%f")`.

Если ученик понимает эту страницу, он уже может нормально вызывать функции и читать CDECL-фрагменты.
