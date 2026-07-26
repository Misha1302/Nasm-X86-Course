---
layout: home

hero:
  name: "NASM x86 для олимпиадников"
  text: "C++ → IA-32 без лишней магии"
  tagline: "Самостоятельный курс: главы, transfer-задачи, зеркальные ключи, skill-based checkpoints и необязательный AI-наставник."
  actions:
    - theme: brand
      text: "Самостоятельный маршрут"
      link: "/self_study"
    - theme: alt
      text: "Начать День 01"
      link: "/day_01"
    - theme: alt
      text: "AI-наставник"
      link: "/ai_tutor_prompts"

features:
  - title: "Замкнутый учебный цикл"
    details: "Каждая глава ведёт к TR-XX, зеркальному ключу, журналу ошибки и решению о переходе."
  - title: "Проверяемые checkpoints"
    details: "Стабильные CP-ID, отдельные баллы, критические навыки и реальные варианты после частичной ошибки."
  - title: "IA-32 без путаницы с x64"
    details: "eax/esp/ebp, стековые аргументы и CDECL. x86-64 вынесен в следующий трек."
  - title: "Честный AI-статус"
    details: "Промпты и eval-кейсы есть, но provider считается проверенным только после сохранённого live-run."
---

# Как проходить курс

Основной цикл:

```text
глава → TR-XX → диагностический ключ → исправление → отложенное повторение
                         ↓
                    checkpoint
```

Начни со страницы [Как пройти курс самостоятельно](/self_study).

## Быстрый старт

| Нужно | Открыть |
|---|---|
| Пройти курс без преподавателя | [Самостоятельный маршрут](/self_study) |
| Решить новую задачу | [Рабочая тетрадь](/transfer_workbook) |
| Проверить transfer | [Диагностические ключи](/transfer_keys) |
| Пройти skill gate | [Контрольные точки](/checkpoints) |
| Поставить баллы и решить вариант | [Ключи checkpoints](/checkpoint_keys) |
| Учиться вместе с моделью | [AI-наставник](/ai_tutor_prompts) |
| Проверить модель по кейсам | [AI-eval](/ai_tutor_eval) |
| Разбить День 10 | [Пять занятий Дня 10](/day_10_learning_path) |
| Понять решение задач | [Как решать задачи](/how_to_solve_tasks) |
| Найти типовую ошибку | [Карточки ошибок](/debug_cards) |
| Проверить state в debugger | [GDB](/debugging_with_gdb) |
| Открыть всё одним файлом | [Полный самостоятельный учебник](/textbook) |

## Цикл одной главы

1. Выполни `Входные знания`.
2. Нарисуй главную модель состояния.
3. Разбери пример и практику.
4. Открой `Следующий шаг` в конце главы.
5. Реши соответствующий `TR-XX` без ключа.
6. Проверь зеркальный ключ и запиши нарушенный инвариант.
7. При локальной ошибке реши новый вариант; при сломанной модели вернись к prerequisite.
8. На следующий день выполни короткое воспроизведение без конспекта.

## Контрольные точки

| Блок | Gate |
|---|---|
| Дни 01–04 | [Checkpoint 1](/checkpoints#checkpoint-1-после-дня-04) |
| Дни 05–10 | [Checkpoint 2](/checkpoints#checkpoint-2-после-дня-10) |
| Дни 11–15 | [Checkpoint 3](/checkpoints#checkpoint-3-после-дня-15) |
| Дни 16–19 | [Checkpoint 4](/checkpoints#checkpoint-4-после-дня-19) |
| Дни 20–23 | [Checkpoint 5](/checkpoints#checkpoint-5-после-дня-23) |
| День 24 | [Checkpoint 6](/checkpoints#checkpoint-6-после-дня-24) |

Каждый checkpoint объявляет максимум, проходной балл и критические `CP-ID`. Сильный ответ по одной теме не компенсирует ноль в центральном инварианте другой темы.

## Ускоренные маршруты

### Route A — Spring-01

1. [День 05](/day_05) — address/value.
2. [День 06](/day_06) — libc.
3. [Дни 07–09](/day_07) — arithmetic, extension, division.
4. [День 10](/day_10) через [пять сессий](/day_10_learning_path).
5. `TR-05`…`TR-10` и Checkpoint 2.

### Route B — листинги и ABI

1. [Дни 11–15](/day_11) — flags, control flow, switch, addressing.
2. `TR-11`…`TR-15` и Checkpoint 3.
3. [Дни 16–19](/day_16) — stack, CDECL, reverse, structures.
4. `TR-16`…`TR-19` и Checkpoint 4.

### Route C — runtime и FPU

1. [Дни 20–23](/day_20) — startup, safety, floating point, x87.
2. `TR-20`…`TR-23` и Checkpoint 5.
3. [День 24](/day_24), `TR-24`, Checkpoint 6.
4. [День 25](/day_25) — mock exam.

## AI-наставник

Prompt pack поддерживает guided learning, strict exam, confusion recovery, solution review и short-context режим. Но совместимость с ChatGPT, DeepSeek или другой моделью не выводится из названия. Текущий evidence status и 10 поведенческих кейсов находятся на странице [Проверка AI-наставника](/ai_tutor_eval).

## Локальный запуск

```bash
npm install
npm run docs:dev
```

Перед публикацией:

```bash
python3 scripts/generate_course_docs.py
python3 scripts/validate_course.py
npm run docs:build
```
