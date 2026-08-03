#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CONTRACT="$ROOT/scripts/executable_contract.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

need() {
    command -v "$1" >/dev/null 2>&1 || {
        printf 'ASM-TOOL-MISSING: %s\n' "$1" >&2
        exit 2
    }
}
need python3
need nasm
need gcc
need nm

mapfile -t records < <(python3 - "$CONTRACT" <<'PYBLOCK'
import json, sys
from pathlib import Path
contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for rel, data in sorted(contract["blocks"].items()):
    print("\x1f".join((rel, data["class"], data.get("golden", ""), data.get("expected", ""))))
PYBLOCK
)

link_object() {
    local obj="$1" out="$2"
    if nm "$obj" | grep -Eq '[[:space:]]_start$'; then
        ld -m elf_i386 "$obj" -o "$out"
    else
        gcc -m32 -g -no-pie -Wl,-z,noexecstack "$obj" -o "$out"
    fi
}

run_special_harness() {
    local name="$1" obj="$2" exe="$3"
    case "$name" in
        10_branchless_ceil)
            cat > "$TMP/${name}_harness.c" <<'CEND'
#include <stdint.h>
#include <stdio.h>
extern void branchless_ceil(void);

static uint32_t call_branchless_ceil(uint32_t a, uint32_t b) {
    __asm__ volatile (
        "call branchless_ceil"
        : "+a"(a), "+c"(b)
        :
        : "edx", "cc", "memory"
    );
    return a;
}

int main(void) {
    static const uint32_t values[] = {0u, 1u, 2u, 0x7fffffffu, 0x80000000u, 0xffffffffu};
    for (unsigned i = 0; i < sizeof values / sizeof values[0]; ++i) {
        printf("%u:%u\n", values[i], call_branchless_ceil(values[i], 0xffffffffu));
    }
    return 0;
}
CEND
            gcc -m32 -g -no-pie -Wl,-z,noexecstack "$TMP/${name}_harness.c" "$obj" -o "$exe"
            return 0
            ;;
        13_x87_order)
            cat > "$TMP/${name}_harness.c" <<'CEND'
#include <stdio.h>
extern double expr(void);
int main(void) {
    printf("%.1f\n", expr());
    return 0;
}
CEND
            gcc -m32 -g -no-pie -Wl,-z,noexecstack "$TMP/${name}_harness.c" "$obj" -o "$exe"
            return 0
            ;;
    esac
    return 1
}

count=0
for record in "${records[@]}"; do
    IFS=$'\x1f' read -r rel class golden expected <<<"$record"
    file="$ROOT/$rel"
    name="$(basename "$file" .asm)"
    obj="$TMP/$name.o"
    exe="$TMP/$name"
    out="$TMP/$name.out"

    test -f "$file" || { printf 'ASM-MISSING: %s\n' "$rel" >&2; exit 1; }
    nasm -f elf32 -g -F dwarf "$file" -o "$obj"

    case "$class" in
        TRACE_ONLY|FRAGMENT|PSEUDOCODE|COMPILE)
            ;;
        RUN)
            if ! run_special_harness "$name" "$obj" "$exe"; then
                link_object "$obj" "$exe"
            fi
            "$exe" > "$out"
            test -n "$golden" || { printf 'ASM-GOLDEN-MISSING: %s\n' "$rel" >&2; exit 1; }
            diff -u "$ROOT/$golden" "$out"
            ;;
        NEGATIVE)
            link_object "$obj" "$exe"
            python3 - "$exe" "$out" "$expected" "$rel" <<'PYNEG'
import signal
import subprocess
import sys
from pathlib import Path

exe, out, expected, rel = sys.argv[1:]
with Path(out).open("wb") as stream:
    result = subprocess.run(
        [exe],
        stdout=stream,
        stderr=subprocess.STDOUT,
        check=False,
    )

if expected == "SIGFPE":
    wanted = -int(signal.SIGFPE)
    if result.returncode != wanted:
        raise SystemExit(
            f"ASM-NEGATIVE: {rel} expected SIGFPE return {wanted}, "
            f"got {result.returncode}"
        )
elif result.returncode == 0:
    raise SystemExit(f"ASM-NEGATIVE: {rel} unexpectedly succeeded")
PYNEG
            ;;
        *)
            printf 'ASM-CLASS: unsupported class %s for %s\n' "$class" "$rel" >&2
            exit 1
            ;;
    esac
    printf 'ASM_EXAMPLE=%s CLASS=%s RESULT=PASS\n' "$rel" "$class"
    count=$((count + 1))
done
printf 'ASM_EXAMPLES_TOTAL=%d\n' "$count"
printf 'ASM_EXAMPLES_SUITE=PASS\n'
