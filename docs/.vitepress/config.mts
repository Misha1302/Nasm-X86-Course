import { defineConfig } from "vitepress";

export default defineConfig({
    base: "/Nasm-X86-Course/",
    title: "NASM x86 для олимпиадников",
    description: "Самостоятельный курс NASM IA-32: главы, transfer-практика, checkpoints и AI-наставник",

    themeConfig: {
        nav: [
            { text: "Самостоятельно", link: "/self_study" },
            { text: "Курс", link: "/day_01" },
            { text: "Тетрадь", link: "/transfer_workbook" },
            { text: "Контроль", link: "/checkpoints" },
            { text: "AI-наставник", link: "/ai_tutor_prompts" },
            { text: "Паттерны", link: "/patterns/" },
            { text: "Задачи", link: "/tasks/" },
            { text: "Финал", link: "/day_25" }
        ],

        sidebar: [
            {
                text: "Как учиться",
                items: [
                    { text: "Старт", link: "/" },
                    { text: "Самостоятельный маршрут", link: "/self_study" },
                    { text: "Рабочая тетрадь", link: "/transfer_workbook" },
                    { text: "Ключи тетради", link: "/transfer_keys" },
                    { text: "Контрольные точки", link: "/checkpoints" },
                    { text: "Ключи checkpoints", link: "/checkpoint_keys" },
                    { text: "AI-наставник", link: "/ai_tutor_prompts" },
                    { text: "Пять занятий Дня 10", link: "/day_10_learning_path" },
                    { text: "Как решать задачи", link: "/how_to_solve_tasks" },
                    { text: "Карточки ошибок", link: "/debug_cards" },
                    { text: "Отладка в GDB", link: "/debugging_with_gdb" },
                    { text: "Поддерживаемые среды", link: "/support_matrix" },
                    { text: "Статус структуры", link: "/course_migration" },
                    { text: "Стиль глав курса", link: "/course_style" }
                ]
            },
            {
                text: "База",
                items: [
                    { text: "День 01 — зачем asm", link: "/day_01" },
                    { text: "День 02 — сборка", link: "/day_02" },
                    { text: "День 03 — CPU и инструкции", link: "/day_03" },
                    { text: "День 04 — регистры", link: "/day_04" },
                    { text: "Checkpoint 1", link: "/checkpoints#checkpoint-1-после-дня-04" },
                    { text: "День 05 — память", link: "/day_05" },
                    { text: "День 06 — ввод/вывод", link: "/day_06" }
                ]
            },
            {
                text: "Spring-01 и арифметика",
                items: [
                    { text: "День 07 — арифметика", link: "/day_07" },
                    { text: "День 08 — расширение", link: "/day_08" },
                    { text: "День 09 — деление", link: "/day_09" },
                    { text: "День 10 — branchless", link: "/day_10" },
                    { text: "Маршрут Дня 10", link: "/day_10_learning_path" },
                    { text: "Checkpoint 2", link: "/checkpoints#checkpoint-2-после-дня-10" }
                ]
            },
            {
                text: "Control flow и адресация",
                items: [
                    { text: "День 11 — EFLAGS", link: "/day_11" },
                    { text: "День 12 — cmp/test/jcc", link: "/day_12" },
                    { text: "День 13 — if и циклы", link: "/day_13" },
                    { text: "День 14 — switch", link: "/day_14" },
                    { text: "День 15 — адресация", link: "/day_15" },
                    { text: "Checkpoint 3", link: "/checkpoints#checkpoint-3-после-дня-15" }
                ]
            },
            {
                text: "Стек, ABI и данные",
                items: [
                    { text: "День 16 — стек", link: "/day_16" },
                    { text: "День 17 — CDECL", link: "/day_17" },
                    { text: "День 18 — reverse", link: "/day_18" },
                    { text: "День 19 — структуры", link: "/day_19" },
                    { text: "Checkpoint 4", link: "/checkpoints#checkpoint-4-после-дня-19" }
                ]
            },
            {
                text: "Runtime, safety и FPU",
                items: [
                    { text: "День 20 — до main", link: "/day_20" },
                    { text: "День 21 — memory safety", link: "/day_21" },
                    { text: "День 22 — floating point", link: "/day_22" },
                    { text: "День 23 — x87", link: "/day_23" },
                    { text: "Практика — double", link: "/fpu_double" },
                    { text: "Checkpoint 5", link: "/checkpoints#checkpoint-5-после-дня-23" },
                    { text: "День 24 — C++ object model", link: "/day_24" },
                    { text: "Checkpoint 6", link: "/checkpoints#checkpoint-6-после-дня-24" },
                    { text: "День 25 — mock exam", link: "/day_25" },
                    { text: "После IA-32: x86-64", link: "/modern_x86_64_next" }
                ]
            },
            {
                text: "Экзаменационные паттерны",
                items: [
                    { text: "Обзор", link: "/patterns/" },
                    { text: "Branchless-маски", link: "/patterns/branchless" },
                    { text: "Битовые циклы", link: "/patterns/bit_counting" },
                    { text: "Десятичные алгоритмы", link: "/patterns/decimal" },
                    { text: "Рекурсия", link: "/patterns/recursion" },
                    { text: "libc и alignment", link: "/patterns/libc_alignment" },
                    { text: "Строки и файлы", link: "/patterns/strings_files" },
                    { text: "Массивная связность", link: "/patterns/array_linked_list" },
                    { text: "Advanced stack", link: "/patterns/advanced_stack" },
                    { text: "Big integer", link: "/patterns/bigint" }
                ]
            },
            {
                text: "Задачи Spring-01",
                items: [
                    { text: "Обзор задач", link: "/tasks/" },
                    { text: "Сложные задачи", link: "/tasks/hard" },
                    { text: "01-4 Книжки", link: "/tasks/spring-01/01-04-books" },
                    { text: "01-8 Masked merge", link: "/tasks/spring-01/01-08-masked-merge" },
                    { text: "01-14 Огород", link: "/tasks/spring-01/01-14-garden" },
                    { text: "01-15 Площадь", link: "/tasks/spring-01/01-15-triangle-area" },
                    { text: "01-16 Система", link: "/tasks/spring-01/01-16-bit-system" }
                ]
            },
            {
                text: "Шпаргалки",
                items: [
                    { text: "C ABI / CDECL", link: "/c_abi" },
                    { text: "Справочник инструкций", link: "/instruction_reference" },
                    { text: "Популярные инструкции", link: "/popular_instructions" },
                    { text: "Шаблоны кода", link: "/code_patterns" },
                    { text: "Полный учебник", link: "/textbook" }
                ]
            }
        ],

        search: {
            provider: "local"
        }
    }
});
