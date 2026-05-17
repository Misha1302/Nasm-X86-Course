# 04-7. Неостросоциальные строки

## Коротко

Количество строк небольшое. Можно хранить уже встреченные строки и сравнивать через `strcmp`.

<details>
<summary>Идея решения</summary>

Для каждой новой строки:

```text
found = false
for each saved string:
    if strcmp(saved, current) == 0:
        found = true

if not found:
    copy current into saved list
    answer++
```

Длина строки до 10, удобно выделить по 16 байт на строку.

</details>

## Где может сломаться

- сравнивать адреса, а не содержимое;
- забыть нулевой байт строки;
- неверно считать адрес `strings + i*16`;
- забыть alignment перед `strcmp`/`scanf`.

## Где в курсе

- День 15: массивы;
- [Строки и файлы](/patterns/strings_files);
- [libc и alignment](/patterns/libc_alignment).
