#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("validate_course.py")
text = path.read_text(encoding="utf-8")

old_block = '''for rel in ("docs/c_abi.md", "docs/day_17.md", "docs/debug_cards.md"):
    source = (ROOT / rel).read_text(encoding="utf-8")
    if re.search(
        r"push (eax|ecx|edx).*?sub esp, 8.*?call printf.*?add esp, 16.*?pop \\1",
        source,
        flags=re.S,
    ):
        errors.append(f"saved dword was omitted from call-site padding calculation: {rel}")'''

new_block = '''def has_saved_dword_alignment_bug(source: str) -> bool:
    lines = source.splitlines()
    for index, line in enumerate(lines):
        save = re.match(r"^[ \\t]*push (?P<reg>eax|ecx|edx)(?:[ \\t]*;.*)?$", line)
        if save is None:
            continue
        register = save.group("reg")
        sub_seen = call_seen = cleanup_seen = False
        for candidate in lines[index + 1 : min(len(lines), index + 20)]:
            stripped = candidate.strip()
            if not sub_seen and stripped.startswith("sub esp, 8"):
                sub_seen = True
            elif sub_seen and not call_seen and stripped == "call printf":
                call_seen = True
            elif call_seen and not cleanup_seen and stripped == "add esp, 16":
                cleanup_seen = True
            elif cleanup_seen and re.match(rf"pop {register}(?:[ \\t]*;.*)?$", stripped):
                return True
    return False


for rel in ("docs/c_abi.md", "docs/day_17.md", "docs/debug_cards.md"):
    source = (ROOT / rel).read_text(encoding="utf-8")
    if has_saved_dword_alignment_bug(source):
        errors.append(f"saved dword was omitted from call-site padding calculation: {rel}")'''

count = text.count(old_block)
if count != 1:
    raise SystemExit(f"expected one broad saved-register validator block, found {count}")
path.write_text(text.replace(old_block, new_block, 1), encoding="utf-8")
