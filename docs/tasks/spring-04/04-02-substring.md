# 04-2. Поиск подстроки в строке

## Коротко

Проще всего использовать `strstr`: проверить `s1` в `s2`, потом `s2` в `s1`.

<details>
<summary>Идея решения</summary>

Читаем две строки в буферы.

```text
if strstr(s2, s1) != NULL -> print "1 2"
else if strstr(s1, s2) != NULL -> print "2 1"
else -> print "0"
```

Порядок аргументов `strstr(haystack, needle)` важен.

</details>

## Где может сломаться

- перепутать `haystack` и `needle`;
- сделать буфер без места под `0`;
- забыть 16-byte alignment перед libc;
- сравнивать строки вручную с off-by-one.

## Где в курсе

- [Строки и файлы](/patterns/strings_files);
- [libc и alignment](/patterns/libc_alignment).
