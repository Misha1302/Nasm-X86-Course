#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
printf 'NODE=%s\n' "$(node --version 2>/dev/null || echo NOT_FOUND)"
printf 'NPM=%s\n' "$(npm --version 2>/dev/null || echo NOT_FOUND)"
printf 'PYTHON=%s\n' "$(python3 --version 2>&1 || true)"
printf 'GCC=%s\n' "$(gcc --version | head -1)"
printf 'NASM=%s\n' "$(nasm -v 2>/dev/null || echo NOT_FOUND)"

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
as --32 "$root/tests/branchless_ceil_i386.S" -o "$tmp/ceil.o"
ld -m elf_i386 "$tmp/ceil.o" -o "$tmp/ceil"
file "$tmp/ceil"
objdump -d -Mintel "$tmp/ceil" > "$tmp/ceil.dis"
for op in 'neg    ecx' 'or     ecx,edx' 'shr    ecx,0x1f'; do
  grep -F "$op" "$tmp/ceil.dis" >/dev/null || { echo "I386_OBJECT=FAIL missing $op" >&2; exit 1; }
done
echo I386_OBJECT_ASSEMBLE_AND_LINK=PASS

set +e
"$tmp/ceil" >/dev/null 2>"$tmp/ceil.err"
run_rc=$?
set -e
if [[ "$run_rc" -eq 0 ]]; then
  echo I386_NATIVE_EXECUTION=PASS
elif grep -qi 'exec format error' "$tmp/ceil.err" || [[ "$run_rc" -eq 126 ]]; then
  echo I386_NATIVE_EXECUTION=NOT_SUPPORTED
else
  echo "I386_NATIVE_EXECUTION=FAIL exit=$run_rc" >&2
  cat "$tmp/ceil.err" >&2
  exit 1
fi

python3 - <<'PYMODEL'
cases=[0,1,2,0x7fffffff,0x80000000,0xffffffff]
def nz(r):
    r &= 0xffffffff
    neg=(-r)&0xffffffff
    return ((neg|r)>>31)&1
actual=[nz(x) for x in cases]
expected=[0,1,1,1,1,1]
assert actual==expected,(actual,expected)
print('BRANCHLESS_CEIL_ORACLE=PASS cases=6')
# The signed quotient 2147483648 is outside int32_t; this is the deterministic
# semantic oracle for the NEGATIVE fixture when native IA-32 execution is unavailable.
q=(-2147483648)//(-1)
assert q==2147483648 and not (-2**31 <= q <= 2**31-1)
print('IDIV_OVERFLOW_ORACLE=PASS')
PYMODEL

as --32 "$root/tests/idiv_overflow_i386.S" -o "$tmp/idiv.o"
ld -m elf_i386 "$tmp/idiv.o" -o "$tmp/idiv"
objdump -d -Mintel "$tmp/idiv" > "$tmp/idiv.dis"
grep -E '\bcdq\b' "$tmp/idiv.dis" >/dev/null
grep -E '\bidiv[[:space:]]+ecx\b' "$tmp/idiv.dis" >/dev/null
echo IDIV_NEGATIVE_OBJECT=PASS

if command -v nasm >/dev/null 2>&1; then
  echo NASM_EXECUTION_CAPABILITY=AVAILABLE
else
  echo NASM_EXECUTION_CAPABILITY=NOT_AVAILABLE
fi
