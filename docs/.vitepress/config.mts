import { defineConfig } from "vitepress";

export default defineConfig({
    base: "/Nasm-X86-Course/",
    title: "NASM x86 для олимпиадников",
    description: "C++ → IA-32: NASM, память, стек, флаги, CDECL и учебные задачи",

    themeConfig: {
        nav: [
            { text: "Старт", link: "/" },
            { text: "Как решать", link: "/how_to_solve_tasks" },
            { text: "Ошибки", link: "/debug_cards" },
            { text: "Домашки", link: "/day_10" },
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
                text: "Домашки 01-7…01-10",
                items: [
                    { text: "День 07 — арифметика", link: "/day_07" },
                    { text: "День 08 — расширение знака", link: "/day_08" },
                    { text: "День 09 — деление", link: "/day_09" },
                    { text: "День 10 — биты и маски", link: "/day_10" }
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
