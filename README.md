# NASM x86 для олимпиадников на C++

Самостоятельный учебник по NASM IA-32: от модели процессора и памяти до CDECL, reverse engineering, структур, x87 и C++ object model.

> Ты уже умеешь C++. Теперь учимся видеть, как код выглядит глазами процессора IA-32.

## Что делает курс самостоятельным

Для каждого из 25 дней есть:

- операциональные входные знания и маршрут возврата;
- объяснение через состояние регистров, памяти, флагов и стека;
- практика внутри главы;
- новая задача `TR-XX` в [рабочей тетради](docs/transfer_workbook.md);
- зеркальный [диагностический ключ](docs/transfer_keys.md);
- явный следующий шаг непосредственно в конце главы;
- шесть [контрольных точек](docs/checkpoints.md) со стабильными `CP`-ID;
- зеркальные [рубрики и дополнительные варианты](docs/checkpoint_keys.md);
- [самостоятельный маршрут](docs/self_study.md) с интервальным повторением и журналом ошибок;
- необязательный [AI-наставник](docs/ai_tutor_prompts.md).

Главное правило:

> Если ты не можешь нарисовать состояние машины и объяснить нарушенный инвариант, тему рано считать закрытой.

## AI-наставник без недоказанных обещаний

Промпты рассчитаны на разные модели, включая ChatGPT и DeepSeek, но конкретная модель считается проверенной только после сохранённого provider-run. Структурный CI и набор кейсов находятся здесь:

- [промпты](docs/ai_tutor_prompts.md);
- [протокол проверки](docs/ai_tutor_eval.md);
- `evals/ai_tutor_cases.json`.

Без live-run статус — `STRUCTURALLY_VALID`, а не `BEHAVIORALLY_VERIFIED`.

## Формат и границы

- NASM x86 / IA-32 без смешения с x86-64 ABI;
- Linux CLI или SASM;
- `nasm -f elf32` и `gcc -m32 -no-pie`;
- сначала Spring-01: 01-4, 01-8, 01-14, 01-15, 01-16;
- затем flags, control flow, stack, CDECL, addressing, reverse, structures, safety, floating point и x87;
- современный x86-64 вынесен в отдельный следующий маршрут.

## Начать обучение

1. Открой [самостоятельный маршрут](docs/self_study.md).
2. Проверь [поддерживаемую среду](docs/support_matrix.md).
3. Начни с [Дня 01](docs/day_01.md).
4. После главы перейди по её блоку `Следующий шаг` к соответствующему `TR-XX`.
5. После блока пройди checkpoint и оцени каждый `CP`-ID отдельно.

День 10 проходится как [пять отдельных занятий](docs/day_10_learning_path.md), а не как один длинный подход.

## Основные страницы

| Страница | Назначение |
|---|---|
| [Самостоятельный маршрут](docs/self_study.md) | учебный цикл и условия перехода |
| [Рабочая тетрадь](docs/transfer_workbook.md) | 25 задач `TR-01`…`TR-25` |
| [Ключи тетради](docs/transfer_keys.md) | зеркальные диагностические ключи |
| [Контрольные точки](docs/checkpoints.md) | шесть skill gates |
| [Ключи checkpoints](docs/checkpoint_keys.md) | scoring, диагностика и варианты |
| [AI-наставник](docs/ai_tutor_prompts.md) | guided learning, exam, recovery и review |
| [Проверка AI-наставника](docs/ai_tutor_eval.md) | provider-backed eval contract |
| Generated route `/textbook` | полный самостоятельный учебник; создаётся перед VitePress build |
| [Closed-book workbook](docs/closed_book_workbook.md) | практика без встроенных ответов; generated перед build |
| [Как решать задачи](docs/how_to_solve_tasks.md) | рабочий алгоритм решения |
| [Карточки ошибок](docs/debug_cards.md) | типовые дефекты |
| [Отладка в GDB](docs/debugging_with_gdb.md) | проверка состояния |
| [Справочник инструкций](docs/instruction_reference.md) | канонический справочник |
| [C ABI / CDECL](docs/c_abi.md) | соглашение вызова |

`docs/textbook.md` и `docs/course_migration.md` — generated artifacts. Они намеренно игнорируются Git и создаются командой `python3 scripts/generate_course_docs.py` либо автоматически перед сборкой сайта.

## Проверяемые примеры

Ключевые фрагменты находятся в `examples/*.asm` и имеют ожидаемый вывод в `examples/expected/*.txt`.

```bash
for file in examples/*.asm; do
    name="$(basename "$file" .asm)"
    nasm -f elf32 "$file" -o "/tmp/$name.o"
    gcc -m32 -no-pie "/tmp/$name.o" -o "/tmp/$name"
    "/tmp/$name"
done
```

Базовая команда:

```bash
nasm -f elf32 main.asm -o main.o
gcc -m32 -no-pie main.o -o main
./main
```

`-no-pie` используется потому, что ранние примеры работают с простыми абсолютными адресами. PIE/GOT/PLT не смешиваются с первой учебной моделью.

## Проверка курса

```bash
python3 scripts/generate_course_docs.py
python3 scripts/validate_course.py
npm ci
npm run docs:build
```

Валидация проверяет:

- структуру всех 25 глав и точные `TR-XX`-переходы;
- зеркальность task/key ID;
- вычислимость checkpoint scoring;
- критические ID и дополнительные варианты;
- Markdown files и anchors;
- AI prompt/eval contract;
- полный generated textbook;
- технические границы и исполняемые NASM-примеры.

## Где ассемблер нужен сегодня

Ассемблер используют точечно там, где нужны конкретная архитектурная инструкция, контроль ABI/машинного состояния или измеренная оптимизация горячего участка: системное программирование, компиляторы и JIT, runtime-библиотеки, libc, кодеки, криптография, reverse engineering, embedded и low-latency код.

Правильный порядок оптимизации:

```text
измерить → изучить дизассемблирование → найти bottleneck → решить, нужен ли ручной asm
```
