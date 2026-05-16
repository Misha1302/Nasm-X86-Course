# День 20. Что происходит до `main` и после него

## Опора на материалы ВШЭ

`Slides2026-0xC.pdf`: `_start`, `__libc_start_main`, initial stack, `.init_array`, `.fini_array`, `objdump`.

## Зачем этот день

В C++ кажется, что программа начинается с `main`. Это удобная иллюзия. На самом деле до `main` уже поработали loader, `_start` и libc.

## Главная мысль

Путь запуска:

```text
OS loader
   |
   v
_start
   |
   v
__libc_start_main(...)
   |
   v
constructors / init
   |
   v
main(argc, argv, envp)
   |
   v
destructors / fini
   |
   v
exit
```

## Что лежит на старте

ОС загружает программу, готовит память процесса и начальный стек. Там можно найти:

- `argc`;
- `argv`;
- `envp`;
- служебные данные загрузчика.

Потом стартовый код вызывает `main` нормальным способом.

## Почему это важно

Когда ты пишешь:

```asm
global main
```

ты не делаешь `main` самой первой инструкцией процесса. Ты просто говоришь линкеру/libc: “вот пользовательская функция main”.

## Команды для наблюдения

```bash
objdump -h main
objdump -d -M intel main
objdump -s -j .init_array main
objdump -s -j .fini_array main
```

## Таблица стадий

| Stage | Artifact/action |
|---|---|
| preprocessing | expanded source |
| compilation | assembly |
| assembling | object `.o` |
| linking | executable |
| loading | process in memory |
| startup | `_start`, libc |
| user code | `main` |

## Мини-челленджи

1. Найди `_start` в `objdump`.
2. Найди `main` в `objdump`.
3. Объясни роль `__libc_start_main`.
4. Почему constructors могут выполниться до `main`?

<details>
<summary>Подсказки</summary>

`__libc_start_main` — функция libc, которая подготавливает запуск пользовательского `main`, вызывает init-функции и обеспечивает корректный выход.

</details>

---
