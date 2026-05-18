import { defineConfig } from "vitepress";

export default defineConfig({
    base: "/Nasm-X86-Course/",
    title: "NASM x86 для олимпиадников",
    description: "C++ → IA-32: NASM, память, стек, флаги, CDECL и учебные задачи",

    themeConfig: {
        nav: [
            { text: "Старт", link: "/" },
            { text: "Как решать", link: "/how_to_solve_tasks" },
            { text: "Паттерны", link: "/patterns/" },
            { text: "Идеи задач", link: "/tasks/" },
            { text: "Сложные", link: "/tasks/hard" },
            { text: "Ошибки", link: "/debug_cards" },
            { text: "C ABI", link: "/c_abi" },
            { text: "Финал", link: "/day_25" }
        ],

        sidebar: [
            {
                text: "Как учиться",
                items: [
                    { text: "Старт", link: "/" },
                    { text: "Как решать задачи", link: "/how_to_solve_tasks" },
                    { text: "Карточки ошибок", link: "/debug_cards" },
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
                    { text: "День 05 — память", link: "/day_05" },
                    { text: "День 06 — ввод/вывод", link: "/day_06" }
                ]
            },
            {
                text: "Домашки Spring-01",
                items: [
                    { text: "День 07 — арифметика", link: "/day_07" },
                    { text: "День 08 — расширение знака", link: "/day_08" },
                    { text: "День 09 — деление", link: "/day_09" },
                    { text: "День 10 — Spring-01 branchless", link: "/day_10" }
                ]
            },
            {
                text: "Экзаменационное ядро",
                items: [
                    { text: "День 11 — EFLAGS", link: "/day_11" },
                    { text: "День 12 — cmp/test/jcc", link: "/day_12" },
                    { text: "День 13 — if и циклы", link: "/day_13" },
                    { text: "День 14 — switch", link: "/day_14" },
                    { text: "День 15 — адресация", link: "/day_15" },
                    { text: "День 16 — стек", link: "/day_16" },
                    { text: "День 17 — CDECL", link: "/day_17" },
                    { text: "День 18 — reverse", link: "/day_18" },
                    { text: "День 19 — структуры", link: "/day_19" }
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
                text: "Подробные разборы",
                items: [
                    { text: "Сложные задачи", link: "/tasks/hard" }
                ]
            },
            {
                text: "Идеи задач — Spring 01",
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
                text: "Идеи задач — Spring 02",
                items: [
                    { text: "02-3 Экстремумы", link: "/tasks/spring-02/02-03-local-extrema" },
                    { text: "02-6 K битов", link: "/tasks/spring-02/02-06-max-bit-window" },
                    { text: "02-9 Прямоугольник", link: "/tasks/spring-02/02-09-rectangle" },
                    { text: "02-12 Нули лайт", link: "/tasks/spring-02/02-12-binary-zeros-lite" },
                    { text: "02-14 Нули", link: "/tasks/spring-02/02-14-binary-zeros" }
                ]
            },
            {
                text: "Идеи задач — Spring 03/04",
                items: [
                    { text: "03-4 Разворот", link: "/tasks/spring-03/03-04-half-reverse" },
                    { text: "03-5 Палиндромы", link: "/tasks/spring-03/03-05-palindromes" },
                    { text: "03-9 Недостаточные", link: "/tasks/spring-03/03-09-deficient" },
                    { text: "03-10 Дроби", link: "/tasks/spring-03/03-10-fractions" },
                    { text: "03-18 Произведение", link: "/tasks/spring-03/03-18-signed-product" },
                    { text: "04-2 Подстрока", link: "/tasks/spring-04/04-02-substring" },
                    { text: "04-4 Count file", link: "/tasks/spring-04/04-04-count-in-file" },
                    { text: "04-7 Разные строки", link: "/tasks/spring-04/04-07-distinct-strings" },
                    { text: "04-11 Перемешивание", link: "/tasks/spring-04/04-11-two-shuffle" },
                    { text: "04-13 Стек", link: "/tasks/spring-04/04-13-stack-fun" }
                ]
            },
            {
                text: "Финиш",
                items: [
                    { text: "День 20 — до main", link: "/day_20" },
                    { text: "День 21 — memory safety", link: "/day_21" },
                    { text: "День 22 — floating point", link: "/day_22" },
                    { text: "День 23 — x87", link: "/day_23" },
                    { text: "День 24 — C++ object model", link: "/day_24" },
                    { text: "День 25 — mock exam", link: "/day_25" }
                ]
            },
            {
                text: "Шпаргалки",
                items: [
                    { text: "C ABI / CDECL", link: "/c_abi" },
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
