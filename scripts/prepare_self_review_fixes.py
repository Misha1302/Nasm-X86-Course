#!/usr/bin/env python3
from pathlib import Path
import re

path = Path(__file__).with_name("apply_self_review_fixes.py")
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"def patch_saved_value_alignment\(\) -> None:\n.*?\n\ndef patch_day06_contract\(\) -> None:",
    flags=re.S,
)
replacement = '''def patch_saved_value_alignment() -> None:
    for rel in ("docs/c_abi.md", "docs/day_17.md", "docs/debug_cards.md"):
        path = ROOT / rel
        lines = path.read_text(encoding="utf-8").splitlines()
        fixes = 0
        index = 0
        while index < len(lines):
            save = re.match(r"^(?P<i>[ \\t]*)push (?P<reg>eax|ecx|edx)(?:[ \\t]*;.*)?$", lines[index])
            if save is None:
                index += 1
                continue
            indent = save.group("i")
            register = save.group("reg")
            limit = min(len(lines), index + 20)
            sub_index = call_index = cleanup_index = pop_index = None
            for pos in range(index + 1, limit):
                stripped = lines[pos].strip()
                if sub_index is None and stripped.startswith("sub esp, 8"):
                    sub_index = pos
                elif sub_index is not None and call_index is None and stripped == "call printf":
                    call_index = pos
                elif call_index is not None and cleanup_index is None and stripped == "add esp, 16":
                    cleanup_index = pos
                elif cleanup_index is not None and re.match(rf"pop {register}(?:[ \\t]*;.*)?$", stripped):
                    pop_index = pos
                    break
            if None not in (sub_index, call_index, cleanup_index, pop_index):
                lines[sub_index] = indent + "sub esp, 4       ; saved dword + 4 padding + 8 argument bytes = 16"
                lines[cleanup_index] = indent + "add esp, 12"
                fixes += 1
                index = pop_index + 1
            else:
                index += 1
        if rel == "docs/c_abi.md" and fixes < 1:
            raise RuntimeError("saved-value alignment example was not found in c_abi.md")
        write(path, "\\n".join(lines) + "\\n")


def patch_day06_contract() -> None:'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f"saved-value function replacement: expected one match, found {count}")
path.write_text(text, encoding="utf-8")
