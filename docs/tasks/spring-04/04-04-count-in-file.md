# 04-4. Just another simple task

## Коротко

Открыть `data.in`, читать `%u` в цикле, считать успешные чтения.

<details>
<summary>Идея решения</summary>

C-shape:

```c
FILE* f = fopen("data.in", "r");
count = 0;
while (fscanf(f, "%u", &x) == 1) {
    count++;
}
printf("%u", count);
fclose(f);
```

В NASM главный риск — не алгоритм, а правильные вызовы libc и alignment.

</details>

## Где может сломаться

- читать со stdin вместо `data.in`;
- не проверять return value `fscanf`;
- забыть `fclose`;
- сломать alignment перед `fscanf`.

## Где в курсе

- [Строки и файлы](/patterns/strings_files);
- [libc и alignment](/patterns/libc_alignment).
