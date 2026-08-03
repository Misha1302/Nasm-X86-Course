#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CONTRACT="$ROOT/scripts/executable_contract.json"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

need() { command -v "$1" >/dev/null 2>&1 || { printf 'ASM-TOOL-MISSING: %s\n' "$1" >&2; exit 2; }; }
need python3; need nasm; need gcc; need nm; need timeout; need ld

mapfile -t records < <(python3 - "$CONTRACT" <<'PYBLOCK'
import json, sys
from pathlib import Path
c=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
for rel,data in sorted(c['blocks'].items()):
 print('\x1f'.join((rel,data['class'],data.get('golden',''),data.get('expected',''),str(data.get('timeout_seconds',c['default_timeout_seconds'])),data.get('harness',''))))
PYBLOCK
)

link_object() {
 local obj="$1" out="$2"
 if nm "$obj" | grep -Eq '[[:space:]]_start$'; then ld -m elf_i386 "$obj" -o "$out"; else gcc -m32 -g -no-pie -Wl,-z,noexecstack "$obj" -o "$out"; fi
}

run_special_harness() {
 local name="$1" obj="$2" exe="$3" harness="$4"
 case "$harness" in
  branchless_ceil)
   cat > "$TMP/${name}_harness.c" <<'CEND'
#include <stdint.h>
#include <stdio.h>
extern void branchless_ceil(void);
static uint32_t call_branchless_ceil(uint32_t a,uint32_t b){__asm__ volatile("call branchless_ceil":"+a"(a),"+c"(b)::"edx","cc","memory");return a;}
int main(void){static const uint32_t v[]={0u,1u,2u,0x7fffffffu,0x80000000u,0xffffffffu};for(unsigned i=0;i<sizeof v/sizeof v[0];++i)printf("%u:%u\n",v[i],call_branchless_ceil(v[i],0xffffffffu));return 0;}
CEND
   gcc -m32 -g -no-pie -Wl,-z,noexecstack "$TMP/${name}_harness.c" "$obj" -o "$exe"; return 0 ;;
  scanf_alignment)
   cat > "$TMP/${name}_harness.asm" <<'AEND'
BITS 32
global _start
global scanf
extern read_x
section .text
_start:
    and esp, -16
    call read_x
    mov eax, 1
    xor ebx, ebx
    int 0x80
scanf:
    mov eax, esp
    and eax, 15
    cmp eax, 12
    jne .bad
    mov eax, [esp+8]
    test eax, eax
    jz .bad
    mov dword [eax], 123
    mov eax, 1
    ret
.bad:
    mov eax, 1
    mov ebx, 97
    int 0x80
section .note.GNU-stack noalloc noexec nowrite progbits
AEND
   nasm -f elf32 "$TMP/${name}_harness.asm" -o "$TMP/${name}_harness.o"
   ld -m elf_i386 "$TMP/${name}_harness.o" "$obj" -o "$exe"; return 0 ;;
  x87_order)
   cat > "$TMP/${name}_harness.c" <<'CEND'
#include <stdio.h>
extern double expr(void);
int main(void){printf("%.1f\n",expr());return 0;}
CEND
   gcc -m32 -g -no-pie -Wl,-z,noexecstack "$TMP/${name}_harness.c" "$obj" -o "$exe"; return 0 ;;
  "") return 1 ;;
  *) printf 'ASM-HARNESS-CONTRACT: unsupported harness %s for %s\n' "$harness" "$name" >&2; return 2 ;;
 esac
}

count=0
for record in "${records[@]}"; do
 IFS=$'\x1f' read -r rel class golden expected seconds harness <<<"$record"
 file="$ROOT/$rel"; name="$(basename "$file" .asm)"; obj="$TMP/$name.o"; exe="$TMP/$name"; out="$TMP/$name.out"
 test -f "$file" || { printf 'ASM-MISSING: %s\n' "$rel" >&2; exit 1; }
 nasm -f elf32 -g -F dwarf "$file" -o "$obj"
 case "$class" in
  TRACE_ONLY|FRAGMENT|PSEUDOCODE|COMPILE) ;;
  RUN)
   if ! run_special_harness "$name" "$obj" "$exe" "$harness"; then link_object "$obj" "$exe"; fi
   timeout --signal=KILL "${seconds}s" "$exe" > "$out"
   test -n "$golden" || { printf 'ASM-GOLDEN-MISSING: %s\n' "$rel" >&2; exit 1; }
   diff -u "$ROOT/$golden" "$out" ;;
  NEGATIVE)
   [[ "$expected" == SIGFPE ]] || { printf 'ASM-NEGATIVE-CONTRACT: unsupported expected=%s for %s\n' "$expected" "$rel" >&2; exit 1; }
   link_object "$obj" "$exe"
   python3 - "$exe" "$out" "$expected" "$rel" "$seconds" <<'PYNEG'
import signal,subprocess,sys
from pathlib import Path
exe,out,expected,rel,seconds=sys.argv[1:]
try:
 with Path(out).open('wb') as stream: result=subprocess.run([exe],stdout=stream,stderr=subprocess.STDOUT,check=False,timeout=int(seconds))
except subprocess.TimeoutExpired: raise SystemExit(f'ASM-TIMEOUT: {rel} exceeded {seconds}s')
wanted=-int(signal.SIGFPE)
if result.returncode!=wanted: raise SystemExit(f'ASM-NEGATIVE: {rel} expected SIGFPE return {wanted}, got {result.returncode}')
PYNEG
   ;;
  *) printf 'ASM-CLASS: unsupported class %s for %s\n' "$class" "$rel" >&2; exit 1 ;;
 esac
 printf 'ASM_EXAMPLE=%s CLASS=%s RESULT=PASS\n' "$rel" "$class"; count=$((count+1))
done
printf 'ASM_EXAMPLES_TOTAL=%d\n' "$count"
printf 'ASM_EXAMPLES_SUITE=PASS\n'
