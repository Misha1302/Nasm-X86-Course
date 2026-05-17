# 04-13. Веселье со стеком

## Коротко

Это advanced ABI-задача: нужно реализовать `apply` с function pointer и varargs.

<details>
<summary>Идея решения</summary>

`apply(array, length, fn, n, ...)` для каждого элемента массива вызывает `fn`.

Для нужного использования:

```c
apply(array, length, fprintf, 2, stdout, "%d\n");
```

Каждый вызов внутри должен собрать на стеке:

```text
array[i]
"%d\n"
stdout
```

и вызвать `fprintf` через function pointer.

</details>

## Где может сломаться

- неверный порядок push для `fn`;
- потерять varargs после первого вызова;
- не сохранить регистры;
- забыть 16-byte alignment;
- перепутать `n` и `n+1` параметров.

## Где в курсе

- День 17: CDECL;
- [libc и alignment](/patterns/libc_alignment);
- [Advanced stack](/patterns/advanced_stack).
