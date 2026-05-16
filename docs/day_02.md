# День 02. SASM, терминал и сборка без магии

## Опора на материалы ВШЭ

`Slides2026-04.pdf`: SASM, Linux x86/Ubuntu-лаборатория, базовая программа NASM.

## Зачем этот день

SASM удобен: написал код, нажал Run, получил результат. Но если сборка сломалась, нужно понимать, что именно произошло. Сегодня снимаем магию с кнопки Run.

## Главная мысль

Файл `.asm` сам не запускается. Его надо превратить в object file, потом слинковать в executable.

```text
main.asm
   |
   | nasm -f elf32
   v
main.o
   |
   | gcc -m32
   v
main
   |
   | ./main
   v
output
```

## Минимальная программа

```asm
section .text
global main

main:
    xor eax, eax
    ret
```

Она ничего не печатает. Просто возвращает `0` из `main`.

## Сборка из терминала

```bash
nasm -f elf32 main.asm -o main.o
gcc -m32 main.o -o main
./main
echo $?
```

Что здесь происходит:

| Команда | Смысл |
|---|---|
| `nasm -f elf32 main.asm -o main.o` | собрать 32-битный object file |
| `gcc -m32 main.o -o main` | слинковать executable, подключив стартовый код/libc |
| `./main` | запустить программу |
| `echo $?` | посмотреть код возврата |

## Зачем `objdump`

`objdump` показывает, что получилось внутри бинарника:

```bash
objdump -d -M intel main
objdump -h main
objdump -s -j .data main
```

`-M intel` нужен, чтобы синтаксис был ближе к NASM.

## Частая боль: 32-битные библиотеки

Если `gcc -m32` ругается, скорее всего, не хватает 32-битной libc.

Ubuntu/Debian:

```bash
sudo apt install nasm gcc gcc-multilib libc6-dev-i386
```

Fedora:

```bash
sudo dnf install nasm gcc glibc-devel.i686 libgcc.i686
```

## Мини-челленджи

1. Собери минимальную программу через CLI.
2. Найди `main` в `objdump -d -M intel main`.
3. Объясни разницу между `.asm`, `.o`, executable.

<details>
<summary>Ответы / подсказки</summary>

- `.asm` — текст исходника.
- `.o` — object file: машинный код, но ещё не финальная программа.
- executable — файл, который ОС может загрузить и запустить.

</details>

## Что должно остаться в голове

SASM удобен, но терминал даёт контроль. На экзамене и в отладке важно понимать цепочку: `asm → object → executable → process`.

---
