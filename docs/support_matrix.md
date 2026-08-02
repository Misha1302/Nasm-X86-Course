# Поддерживаемые среды

Каноническая модель курса — Linux x86-64 с установленным 32-битным набором инструментов для сборки IA-32 ELF.

Статус разделяет документированную инструкцию и реально выполненную проверку.

| Среда | Статус | Что доказано |
|---|---|---|
| Ubuntu `ubuntu-latest` | **CI-verified** | документация собирается; все `examples/*.asm` компонуются и запускаются с golden output |
| Ubuntu 24.04 x86-64 | основной сценарий | команды соответствуют CI; локальная машина всё равно должна пройти smoke test ниже |
| Debian x86-64 | documented, not CI-verified | ожидаются близкие пакеты; конкретный релиз в CI не проверяется |
| Fedora x86-64 | documented, manually unverified | приведены типовые пакеты, но автоматической проверки Fedora нет |
| WSL2 с Ubuntu | expected compatible, unverified | используется Linux userspace, но отдельный CI-запуск WSL2 отсутствует |
| macOS | через Linux VM/container | Mach-O и системный ABI не совпадают с учебным ELF/CDECL |
| Windows без WSL | ограниченно | SASM может покрыть ранние упражнения; эталонная CLI-сборка остаётся Linux |

## Эталонная локальная проверка

```bash
nasm -v
gcc -m32 -x c -o /tmp/hello32 - <<'C'
int main(void) { return 0; }
C
file /tmp/hello32
/tmp/hello32
```

Успех доказывает только работоспособность локального NASM, компоновщика и 32-битной libc. Он не превращает другую ОС или ABI в каноническую среду курса.

## Типовые пакеты

Ubuntu/Debian:

```bash
sudo apt install nasm gcc gcc-multilib libc6-dev-i386
```

Fedora, названия зависят от версии:

```bash
sudo dnf install nasm gcc glibc-devel.i686 libgcc.i686
```

После установки всегда выполняй smoke test, а не считай наличие пакета доказательством полной совместимости.
