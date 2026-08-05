# Проверка ИИ-наставника

Эта страница отделяет качество инструкции, факт запуска провайдера и семантический результат. Ни наличие prompt-файла, ни успешный HTTP-запрос сами по себе не доказывают корректное поведение модели.

## Текущий статус

| Что проверяется | Статус |
|---|---|
| Структура инструкций | проверяется автоматически |
| Наличие `<task>`, `<chapter>`, `<answer>` | проверяется автоматически |
| Сценарии поведения | хранятся в `evals/ai_tutor_cases.json` |
| Исполняемый provider runner | реализован в `scripts/run_ai_tutor_provider_eval.py` |
| Offline mock-регрессии runner-а | выполняются в CI |
| Реальные запуски ChatGPT | не сохранены |
| Реальные запуски DeepSeek | не сохранены |
| Другие модели | не проверены |
| Provider status | `NOT_RUN` |

До появления сохранённого live-артефакта и отдельной семантической проверки нельзя утверждать, что конкретная модель стабильно соблюдает инструкции.

Структурная проверка не заменяет реальные запуски модели.

## Формат сценария

Одноходовый сценарий содержит задачу и один ответ ученика. Сценарий повторной ошибки содержит массив конкретных последовательных ходов `turns`, а не строку «это третья ошибка» и не служебные placeholder-реплики.

```json
{
  "id": "AI-06-third-failure-prerequisite",
  "turns": [
    {"role": "user", "content": "Сразу после call на вершине первый аргумент"},
    {"role": "assistant", "content": "Какое значение сама call добавляет на стек?"},
    {"role": "user", "content": "Ничего не добавляет"},
    {"role": "assistant", "content": "Нарисуй [esp], [esp+4], [esp+8] и подпиши адрес возврата"},
    {"role": "user", "content": "Отдельного адреса возврата нет"}
  ]
}
```

Стенд передаёт эти ходы в указанном порядке и оценивает следующий ответ модели. Это **curated scripted history**: предыдущие ответы зафиксированы как реалистичный тестовый transcript. Она проверяет реакцию модели на конкретную историю, но не доказывает, что кандидатная модель сама породила качественные предыдущие ответы. Для полной stateful trajectory-проверки понадобился бы отдельный многоходовый запуск, сохраняющий и оценивающий всю траекторию.

Runner отклоняет любую реплику, содержащую `_placeholder`.

## Что проверяют десять сценариев

1. ровно один вопрос за сообщение;
2. отсутствие раннего полного решения;
3. границу IA-32 против x86-64;
4. запрет непроходившего материала;
5. смену представления после повторной ошибки;
6. возврат к prerequisite после третьей ошибки;
7. факт против гипотезы в анализе машинного кода;
8. порядок x87;
9. проверку в той же сессии против интервального повторения;
10. запрос одного недостающего факта.

## Offline-проверка стенда

```bash
python3 tests/test_ai_tutor_provider_eval.py
```

Тест поднимает локальный OpenAI-compatible mock-сервер и проверяет:

- компиляцию всех `10 × 3` запросов;
- получение ровно 30 транскриптов;
- запрет двух, четырёх или другого числа запусков на сценарий;
- отсутствие placeholder-историй в production cases;
- сохранение точных входных сообщений и их SHA-256;
- точное соответствие case/run topology текущим сценариям;
- привязку к текущим case, prompt и adapter SHA-256;
- отказ при подмене сохранённого запроса;
- запрет самовольного объявления семантического `PASS`;
- полноту topology ручной или независимой проверки;
- запрет самопроверки кандидатной моделью;
- проверку реального файла evidence независимого судьи и его SHA-256.

## Live-запуск

Ключ передаётся только через переменную окружения и не сохраняется в артефакте. Release-gate использует **ровно три запуска каждого сценария**. Параметр `--runs` оставлен явным для воспроизводимости, но любое значение кроме `3` отклоняется.

### OpenAI

```bash
export AI_TUTOR_API_KEY='...'
python3 scripts/run_ai_tutor_provider_eval.py run \
  --provider openai \
  --model '<exact-model-id>' \
  --runs 3 \
  --token-limit-field max_completion_tokens \
  --output AI_TUTOR_PROVIDER_EVIDENCE.json
```

### DeepSeek

```bash
export AI_TUTOR_API_KEY='...'
python3 scripts/run_ai_tutor_provider_eval.py run \
  --provider deepseek \
  --model '<exact-model-id>' \
  --runs 3 \
  --token-limit-field max_tokens \
  --output AI_TUTOR_PROVIDER_EVIDENCE.json
```

`--temperature` и `--seed-base` задаются только когда выбранная модель действительно поддерживает эти параметры. Точная модель, параметры, время, полный массив сообщений, полный ответ, usage и digest runner-а сохраняются в evidence-файле.

Проверка полноты захвата:

```bash
python3 scripts/run_ai_tutor_provider_eval.py validate \
  AI_TUTOR_PROVIDER_EVIDENCE.json
```

Эта команда требует точные 10 сценариев, **ровно три** запуска каждого, полный Git SHA и совпадение сохранённых сообщений с текущими case/prompt fixtures. Она доказывает только полноту и целостность provider capture и намеренно выводит:

```text
AI_TUTOR_SEMANTIC_ADJUDICATION=NOT_RUN
```

## Семантическая проверка

Создай точный шаблон для всех `must` и `must_not` каждого запуска:

```bash
python3 scripts/run_ai_tutor_provider_eval.py template \
  AI_TUTOR_PROVIDER_EVIDENCE.json \
  --output AI_TUTOR_ADJUDICATION.json
```

В `reviewer` укажи один из режимов.

### Ручная проверка

```json
{
  "kind": "manual",
  "id": "reviewer-name-or-stable-id",
  "provider": null,
  "model": null,
  "evidence_sha256": null
}
```

После заполнения checks:

```bash
python3 scripts/run_ai_tutor_provider_eval.py score \
  AI_TUTOR_PROVIDER_EVIDENCE.json \
  AI_TUTOR_ADJUDICATION.json \
  --output AI_TUTOR_BEHAVIOR_REPORT.json
```

### Независимая модель-судья

Нужен отдельный сохранённый JSON-артефакт, например `AI_TUTOR_JUDGE_EVIDENCE.json`, с идентичностью судьи и непустым массивом judgments:

```json
{
  "provider": "another-provider",
  "model": "another-model-id",
  "judgments": [
    {"case_id": "AI-01-one-question", "run_index": 1, "notes": "..."}
  ]
}
```

В `reviewer` adjudication-файла должны совпадать provider/model и точный SHA-256 этого файла. Затем:

```bash
python3 scripts/run_ai_tutor_provider_eval.py score \
  AI_TUTOR_PROVIDER_EVIDENCE.json \
  AI_TUTOR_ADJUDICATION.json \
  --judge-evidence AI_TUTOR_JUDGE_EVIDENCE.json \
  --output AI_TUTOR_BEHAVIOR_REPORT.json
```

Scorer сам открывает файл, пересчитывает SHA-256, проверяет provider/model, непустой `judgments` и отличие артефакта от candidate evidence и adjudication. Строка из 64 hex-символов без соответствующего файла больше не является evidence. Кандидатная provider/model-пара не может считаться независимым судьёй самой себя.

Для каждого check замени `UNREVIEWED` на `PASS` или `FAIL` и добавь конкретное evidence-обоснование.

Скоринг fail-closed: отсутствующий запуск, check, verdict, evidence note, несовпадающий digest, отсутствующий judge-файл или число запусков, отличное от трёх, блокируют итог.

## Минимальный provider-backed прогон

```text
10 сценариев × ровно 3 независимых запуска = 30 ответов
```

Для запуска сохраняются:

- provider и точная модель;
- commit инструкции;
- полный массив входных сообщений;
- полный ответ;
- дата, seed/temperature при наличии;
- результаты каждого `must` и `must_not` после отдельной проверки;
- проверяющий или отдельный артефакт независимой модели-судьи.

## Критические ошибки

- раннее полное решение;
- несколько независимых вопросов;
- смешение ABI;
- принятие неверной трассировки x87/CDECL;
- гипотеза, выданная за факт;
- продолжение сложной темы после третьей одинаковой ошибки.

## Порог

При ровно трёх запусках критические сценарии проходят `3/3`, остальные — минимум `2/3`. Этот текст формируется тем же исполняемым контрактом, который считает результат; режимы `4/5` не поддерживаются и не создают скрытого другого порога.

Статическая проверка структуры, успешный mock-тест и полнота provider capture не заменяют семантическую проверку реальных ответов.

## GitHub Actions

Workflow `Capture AI tutor provider evidence` запускается вручную. Для него нужны repository secrets:

- `AI_TUTOR_OPENAI_API_KEY`;
- `AI_TUTOR_DEEPSEEK_API_KEY`.

Workflow сначала проверяет runner локальным mock-тестом, затем сохраняет revision-bearing provider evidence и незаполненный adjudication template как artifact. Он всегда выполняет `10 × 3` запросов и не объявляет поведение модели проверенным до отдельного scoring-прохода.
