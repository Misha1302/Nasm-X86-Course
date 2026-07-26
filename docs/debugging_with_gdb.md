# Отладка NASM в GDB

## За 30 секунд

- Собирай NASM с `-g -F dwarf`, а линковку — с `-g`.
- `start` останавливается около входа в `main`.
- `layout asm` показывает инструкции, `layout regs` — регистры.
- `si` делает один машинный шаг, `ni` проходит вызов целиком.
- `x/16wx $esp` показывает 16 dword на стеке.
- После каждой инструкции сравни ожидаемое состояние с фактическим.

## Сборка для отладки

```bash
nasm -f elf32 -g -F dwarf main.asm -o main.o
gcc -m32 -g -no-pie -Wl,-z,noexecstack main.o -o main
gdb ./main
```

## Минимальный сеанс

```text
set disassembly-flavor intel
start
layout asm
layout regs
si
info registers eax ebx ecx edx esp ebp eflags
x/16wx $esp
```

## Как проверять стек вызова

Перед `call` запиши ожидаемые аргументы и `esp`. После возврата проверь, что CDECL-аргументы удалены правильным `add esp, N`.

```text
p/x $esp
x/12wx $esp
si
```

## Как ловить повреждение памяти

```text
break main
watch x
run
continue
```

Для адресной ошибки остановись перед подозрительной инструкцией и отдельно вычисли базу, индекс, scale и displacement.

## Практика

1. Пройди `examples/06_signed_division.asm` по одной инструкции и проверь `edx:eax` до и после `idiv`.
2. В `examples/07_jump_table.asm` посмотри адрес выбранного элемента таблицы.
3. В `examples/08_x87_printf.asm` используй `info float`, чтобы увидеть x87-стек.

## Чеклист

- [ ] Я умею собрать файл с DWARF-символами.
- [ ] Я вижу регистры и стек до/после инструкции.
- [ ] Я отличаю `si` от `ni`.
- [ ] Я проверяю вычисленный адрес, а не только итоговое падение.
