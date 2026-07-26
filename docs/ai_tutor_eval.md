# Проверка AI-наставника

Эта страница отделяет качество текста промпта от фактического поведения конкретной модели.

## Текущий статус

| Проверка | Статус |
|---|---|
| Структура prompt pack | проверяется CI |
| Наличие `<task>/<chapter>/<answer>` | проверяется CI |
| Наличие recovery-протокола | проверяется CI |
| Поведенческий набор из 10 кейсов | хранится в `evals/ai_tutor_cases.json` |
| Live ChatGPT run | не сохранён в репозитории |
| Live DeepSeek run | не сохранён в репозитории |
| Другие providers | не проверены |

До появления provenance-bearing run нельзя утверждать, что конкретная модель стабильно соблюдает промпт.

## Что проверяют кейсы

1. ровно один вопрос за сообщение;
2. отсутствие полного решения до второй попытки;
3. сохранение IA-32/CDECL boundary;
4. запрет проверки ещё не изученного материала;
5. смену representation после второй ошибки;
6. возврат к prerequisite после третьей ошибки;
7. отделение reverse-engineering facts от hypotheses;
8. порядок operands и глубину x87;
9. различие same-session retrieval и spaced repetition;
10. запрос одного недостающего факта вместо выдумывания условия.

## Воспроизводимая сборка case

Каждый case обязан хранить:

- точный `prompt_heading`, выбирающий один fenced prompt mode;
- `chapter_files` в фиксированном порядке;
- `input_contract.task` и `input_contract.answer`;
- `must`/`must_not` как scoring contract.

Harness собирает полный input только из этих полей и сохраняет его вместе с output. Пустой `chapter_files` допустим только для кейса, который проверяет реакцию на отсутствующее условие. Это делает provider-run повторяемым, но не превращает static fixture в доказательство поведения модели.

## Минимальный provider-run

Для каждого provider/model:

```text
10 кейсов × 3 независимых запуска
```

Сохраняй:

- provider и точный model ID;
- дату и revision prompt page;
- ID кейса и номер запуска;
- полный вход;
- полный ответ модели;
- значения каждого `must` и `must_not`;
- итоговый verdict;
- reviewer и способ проверки.

## Критические провалы

Любой из этих результатов блокирует статус «проверено»:

- ранняя выдача полного решения;
- несколько независимых вопросов одновременно;
- переход на x86-64 ABI;
- принятие неверного x87/CDECL state;
- уверенная high-level reconstruction без evidence;
- выдумывание отсутствующего listing или условия;
- продолжение сложной темы после третьей ошибки без prerequisite recovery.

## Формат результата

```json
{
  "provider": "...",
  "model": "...",
  "prompt_commit": "...",
  "case_id": "AI-01-one-question",
  "run": 1,
  "must": {
    "ask_exactly_one_question": true,
    "not_reveal_full_solution": true
  },
  "must_not": {
    "ask_multiple_independent_questions": true
  },
  "verdict": "PASS"
}
```

Поле `must_not` считается успешным, когда запрещённое поведение **не наблюдалось**; используемый harness должен явно зафиксировать эту семантику.

## Порог

- все критические кейсы должны пройти 3/3;
- остальные — не менее 2/3;
- один authority/boundary failure делает provider status `FAILED`;
- structural CI без live runs даёт только `STRUCTURALLY_VALID`, не `BEHAVIORALLY_VERIFIED`.
