#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("validate_course.py")
text = path.read_text(encoding="utf-8")

start_marker = 'for rel in ("docs/c_abi.md", "docs/day_17.md", "docs/debug_cards.md"):\n'
end_marker = '\nday22_text = (DOCS / "day_22.md").read_text(encoding="utf-8")'
start = text.find(start_marker)
end = text.find(end_marker, start + 1)
if start < 0 or end < 0:
    raise SystemExit(f"saved-register validator boundaries not found: start={start}, end={end}")

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
        errors.append(f"saved dword was omitted from call-site padding calculation: {rel}")
'''

path.write_text(text[:start] + new_block + text[end:], encoding="utf-8")
