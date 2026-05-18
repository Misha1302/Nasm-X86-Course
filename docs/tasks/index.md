# Краткие идеи решений задач

Это не банк готового кода. Это разборы: какая идея нужна, какие темы курса подключить и где обычно ломаются.

Самые трудные задачи вынесены в отдельный список: [подробные разборы сложных задач](/tasks/hard).

## Spring-01

| Задача | Идея |
|---|---|
| [01-4 Книжки](./spring-01/01-04-books) | формула без ветвлений |
| [01-8 Masked merge](./spring-01/01-08-masked-merge) | битовый выбор по маске |
| [01-14 Огород](./spring-01/01-14-garden) | ceil division + branchless выбор |
| [01-15 Площадь треугольника](./spring-01/01-15-triangle-area) | удвоенная площадь + `.0/.5` |
| [01-16 Система уравнений](./spring-01/01-16-bit-system) | решить 4 варианта на каждый бит |

## Spring-02

| Задача | Идея |
|---|---|
| [02-3 Локальные экстремумы](./spring-02/02-03-local-extrema) | массив + сравнение соседей |
| [02-6 K битов](./spring-02/02-06-max-bit-window) | sliding window по битам |
| [02-9 Прямоугольник](./spring-02/02-09-rectangle) | min/max координат + строгие границы |
| [02-12 Двоичные нули лайт](./spring-02/02-12-binary-zeros-lite) | brute force + popcount/bit_length |
| [02-14 Двоичные нули](./spring-02/02-14-binary-zeros) | комбинаторика по битам |

## Spring-03

| Задача | Идея |
|---|---|
| [03-4 Разворот половины](./spring-03/03-04-half-reverse) | рекурсия, печать до/после call |
| [03-5 Палиндромы](./spring-03/03-05-palindromes) | reverse decimal + ровно N шагов |
| [03-9 Недостаточные числа](./spring-03/03-09-deficient) | функция cdecl `is_deficient` |
| [03-10 Дроби](./spring-03/03-10-fractions) | сложение дробей + GCD |
| [03-18 Знаковое произведение](./spring-03/03-18-signed-product) | advanced bigint |

## Spring-04

| Задача | Идея |
|---|---|
| [04-2 Подстрока](./spring-04/04-02-substring) | `strstr` + строки + alignment |
| [04-4 Count integers](./spring-04/04-04-count-in-file) | `fopen/fscanf` |
| [04-7 Различные строки](./spring-04/04-07-distinct-strings) | массив строк + `strcmp` |
| [04-11 2-перемешивание](./spring-04/04-11-two-shuffle) | linked list через массивы |
| [04-13 Веселье со стеком](./spring-04/04-13-stack-fun) | function pointer + varargs |
