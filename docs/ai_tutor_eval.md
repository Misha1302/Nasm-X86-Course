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

Одноходовый сценарий содержит задачу и один ответ ученика. Сценарий повторной ошибки обязан содержать массив последовательных ходов `turns`, а не строку «это третья ошибка».

```json
{
  "id": "AI-06-third-failure-prerequisite",
  "turns": [
    {"role": "user", "content": "первая попытка"},
    {"role": "assistant", "content": "первый ответ"},
    {"role": "user", "content": "вторая попытка"},
    {"role": "assistant", "content": "смена способа объяснения"},
    {"role": "user", "content": "третья попытка"}
  ]
}
```

Стенд передаёт ходы в указанном порядке и оценивает только следующий ответ модели.

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
- получение 30 транскриптов;
- сохранение точных входных сообщений и их SHA-256;
- точное соответствие case/run topology текущим сценариям;
- минимум три запуска каждого сценария;
- привязку к текущим case, prompt и adapter SHA-256;
- отказ при подмене сохранённого запроса;
- запрет самовольного объявления семантического `PASS`;
- полноту topology ручной или независимой проверки.

## Live-запуск

Ключ передаётся только через переменную окружения и не сохраняется в артефакте.

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

Эта команда требует точные 10 сценариев, не менее трёх запусков каждого, полный Git SHA и совпадение сохранённых сообщений с текущими case/prompt fixtures. Она доказывает только полноту и целостность provider capture и намеренно выводит:

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

В `reviewer` укажи:

- `kind: manual` и идентификатор проверяющего; либо
- `kind: independent_model`, provider и модель, отличающиеся от проверяемой пары provider/model.

Для `independent_model` дополнительно обязателен `evidence_sha256` отдельного сохранённого артефакта работы модели-судьи. Кандидатная модель не может считаться независимым судьёй самой себя.

Для каждого check замени `UNREVIEWED` на `PASS` или `FAIL` и добавь конкретное evidence-обоснование. Затем выполни:

```bash
python3 scripts/run_ai_tutor_provider_eval.py score \
  AI_TUTOR_PROVIDER_EVIDENCE.json \
  AI_TUTOR_ADJUDICATION.json \
  --output AI_TUTOR_BEHAVIOR_REPORT.json
```

Скоринг fail-closed: отсутствующий запуск, check, verdict, evidence note, несовпадающий digest или менее трёх запусков сценария блокирует итог.

## Минимальный provider-backed прогон

```text
10 сценариев × 3 независимых запуска
```

Для запуска сохраняются:

- provider и точная модель;
- commit инструкции;
- полный массив входных сообщений;
- полный ответ;
- дата, seed/temperature при наличии;
- результаты каждого `must` и `must_not` после отдельной проверки;
- проверяющий или независимая модель-судья.

## Критические ошибки

- раннее полное решение;
- несколько независимых вопросов;
- смешение ABI;
- принятие неверной трассировки x87/CDECL;
- гипотеза, выданная за факт;
- продолжение сложной темы после третьей одинаковой ошибки.

## Порог

Критические сценарии проходят `3/3`, остальные — минимум `2/3`. Статическая проверка структуры, успешный mock-тест и полнота provider capture не заменяют семантическую проверку реальных ответов.

## GitHub Actions

Workflow `Capture AI tutor provider evidence` запускается вручную. Для него нужны repository secrets:

- `AI_TUTOR_OPENAI_API_KEY`;
- `AI_TUTOR_DEEPSEEK_API_KEY`.

Workflow сначала проверяет runner локальным mock-тестом, затем сохраняет revision-bearing provider evidence и незаполненный adjudication template как artifact. Он не объявляет поведение модели проверенным до отдельного scoring-прохода.
