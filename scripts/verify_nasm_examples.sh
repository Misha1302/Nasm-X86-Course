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
for tool in python3 nasm gcc nm timeout base64; do need "$tool"; done

mapfile -t records < <(python3 - "$CONTRACT" <<'PYBLOCK'
import base64
import json
import sys
from pathlib import Path
contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for rel, data in sorted(contract["blocks"].items()):
    stdin = base64.b64encode(data.get("stdin", "").encode("utf-8")).decode("ascii")
    print("\x1f".join((
        rel,
        data["class"],
        data.get("golden", ""),
        data.get("expected", ""),
        stdin,
        str(data.get("timeout_seconds", 10)),
    )))
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
        14_scanf_call)
            cat > "$TMP/${name}_harness.c" <<'CEND'
#include <stdio.h>
extern int read_x(void);
int main(void) {
    printf("%d\n", read_x());
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
    IFS=$'\x1f' read -r rel class golden expected stdin_b64 timeout_seconds <<<"$record"
    file="$ROOT/$rel"
    name="$(basename "$file" .asm)"
    obj="$TMP/$name.o"
    exe="$TMP/$name"
    out="$TMP/$name.out"
    input="$TMP/$name.in"

    test -f "$file" || { printf 'ASM-MISSING: %s\n' "$rel" >&2; exit 1; }
    [[ "$timeout_seconds" =~ ^[1-9][0-9]*$ ]] || { printf 'ASM-TIMEOUT: invalid timeout for %s\n' "$rel" >&2; exit 1; }
    printf '%s' "$stdin_b64" | base64 -d > "$input"
    nasm -f elf32 -g -F dwarf "$file" -o "$obj"

    case "$class" in
        TRACE_ONLY|FRAGMENT|PSEUDOCODE|COMPILE)
            ;;
        RUN)
            if ! run_special_harness "$name" "$obj" "$exe"; then
                link_object "$obj" "$exe"
            fi
            if ! timeout --signal=KILL "${timeout_seconds}s" "$exe" < "$input" > "$out"; then
                status=$?
                printf 'ASM-RUN: %s exited with status %d or timed out\n' "$rel" "$status" >&2
                exit 1
            fi
            test -n "$golden" || { printf 'ASM-GOLDEN-MISSING: %s\n' "$rel" >&2; exit 1; }
            diff -u "$ROOT/$golden" "$out"
            ;;
        NEGATIVE)
            [[ "$expected" == "SIGFPE" ]] || {
                printf 'ASM-NEGATIVE-EXPECTED: %s has unsupported or missing expected outcome %q\n' "$rel" "$expected" >&2
                exit 1
            }
            link_object "$obj" "$exe"
            python3 - "$exe" "$out" "$expected" "$rel" "$timeout_seconds" <<'PYNEG'
import signal
import subprocess
import sys
from pathlib import Path

exe, out, expected, rel, timeout_seconds = sys.argv[1:]
try:
    with Path(out).open("wb") as stream:
        result = subprocess.run(
            [exe],
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=int(timeout_seconds),
        )
except subprocess.TimeoutExpired as exc:
    raise SystemExit(f"ASM-TIMEOUT: {rel} exceeded {timeout_seconds}s") from exc

if expected != "SIGFPE":
    raise SystemExit(f"ASM-NEGATIVE-EXPECTED: unsupported outcome {expected!r} for {rel}")
wanted = -int(signal.SIGFPE)
if result.returncode != wanted:
    raise SystemExit(
        f"ASM-NEGATIVE: {rel} expected SIGFPE return {wanted}, got {result.returncode}"
    )
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
