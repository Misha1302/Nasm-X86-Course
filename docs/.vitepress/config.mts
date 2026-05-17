import { defineConfig } from 'vitepress';

const courseSidebar = [
  {
    text: 'Учиться по курсу',
    collapsed: false,
    items: [
      { text: 'Главная', link: '/' },
      { text: 'Полный учебник', link: '/textbook' }
    ]
  },
  {
    text: 'Старт курса',
    collapsed: false,
    items: [
      { text: 'День 01. Что происходит при запуске', link: '/day_01' },
      { text: 'День 02. SASM и терминал', link: '/day_02' },
      { text: 'День 03. CPU, память, инструкции', link: '/day_03' },
      { text: 'День 04. Регистры IA-32', link: '/day_04' },
      { text: 'День 05. x и [x]', link: '/day_05' },
      { text: 'День 06. Ввод и вывод', link: '/day_06' }
    ]
  },
  {
    text: 'Арифметика и домашки 01-7…01-10',
    collapsed: false,
    items: [
      { text: 'День 07. add без iadd', link: '/day_07' },
      { text: 'День 08. movsx и movzx', link: '/day_08' },
      { text: 'День 09. mul, imul, div, idiv', link: '/day_09' },
      { text: 'День 10. Биты, маски, домашки', link: '/day_10' }
    ]
  },
  {
    text: 'Флаги, переходы и адресация',
    collapsed: false,
    items: [
      { text: 'День 11. EFLAGS', link: '/day_11' },
      { text: 'День 12. cmp, test, jcc', link: '/day_12' },
      { text: 'День 13. if, циклы, GOTO', link: '/day_13' },
      { text: 'День 14. switch и jump table', link: '/day_14' },
      { text: 'День 15. lea, массивы', link: '/day_15' }
    ]
  },
  {
    text: 'Стек, функции и данные',
    collapsed: false,
    items: [
      { text: 'День 16. push, pop, call, ret', link: '/day_16' },
      { text: 'День 17. Фрейм и CDECL', link: '/day_17' },
      { text: 'День 18. Reverse engineering', link: '/day_18' },
      { text: 'День 19. Структуры', link: '/day_19' }
    ]
  },
  {
    text: 'Системные темы и финал',
    collapsed: false,
    items: [
      { text: 'День 20. До main и после main', link: '/day_20' },
      { text: 'День 21. Безопасность', link: '/day_21' },
      { text: 'День 22. Вещественные числа', link: '/day_22' },
      { text: 'День 23. x87', link: '/day_23' },
      { text: 'День 24. C++ object model', link: '/day_24' },
      { text: 'День 25. Mock exam', link: '/day_25' }
    ]
  }
];

export default defineConfig({
  lang: 'ru-RU',
  title: 'NASM x86 Course',
  description: 'NASM x86 для олимпиадников на C++: живой курс по IA-32 для подготовки к экзамену ВШЭ.',
  base: '/Nasm-X86-Course/',
  cleanUrls: true,
  lastUpdated: true,

  head: [
    ['meta', { name: 'theme-color', content: '#111827' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'NASM x86 для олимпиадников на C++' }],
    ['meta', { property: 'og:description', content: 'Живой учебник по NASM x86 / IA-32: регистры, память, стек, флаги, CDECL и задачи.' }]
  ],

  markdown: {
    lineNumbers: true
  },

  themeConfig: {
    logo: { light: '/logo-light.svg', dark: '/logo-dark.svg' },
    siteTitle: 'NASM x86 Course',

    nav: [
      { text: 'Главная', link: '/' },
      { text: 'Полный учебник', link: '/textbook' },
      { text: 'Начать', link: '/day_01' },
      { text: 'Домашки 01-7…01-10', link: '/day_10' },
      { text: 'Финальная проверка', link: '/day_25' }
    ],

    sidebar: {
      '/': courseSidebar
    },

    outline: {
      level: [2, 3],
      label: 'На странице'
    },

    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: {
                buttonText: 'Поиск',
                buttonAriaLabel: 'Поиск по курсу'
              },
              modal: {
                displayDetails: 'Показать детали',
                resetButtonTitle: 'Сбросить поиск',
                backButtonTitle: 'Закрыть поиск',
                noResultsText: 'Ничего не найдено',
                footer: {
                  selectText: 'выбрать',
                  selectKeyAriaLabel: 'enter',
                  navigateText: 'перейти',
                  navigateUpKeyAriaLabel: 'стрелка вверх',
                  navigateDownKeyAriaLabel: 'стрелка вниз',
                  closeText: 'закрыть',
                  closeKeyAriaLabel: 'escape'
                }
              }
            }
          }
        }
      }
    },

    docFooter: {
      prev: 'Предыдущий день',
      next: 'Следующий день'
    },

    lastUpdated: {
      text: 'Обновлено',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short'
      }
    },

    editLink: {
      pattern: 'https://github.com/Misha1302/Nasm-X86-Course/edit/main/docs/:path',
      text: 'Исправить эту страницу'
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Misha1302/Nasm-X86-Course' }
    ],

    footer: {
      message: 'NASM x86 / IA-32 course for C++ olympiad programmers.',
      copyright: 'Released under the repository license.'
    }
  }
});
