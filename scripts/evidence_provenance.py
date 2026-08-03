from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


def digest_paths(root: Path, paths: Iterable[str | Path]) -> str:
    h = hashlib.sha256()
    normalized = sorted({str(Path(path).as_posix()) for path in paths})
    for rel in normalized:
        path = root / rel
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        if not path.is_file():
            h.update(b"<MISSING>")
        else:
            h.update(hashlib.sha256(path.read_bytes()).digest())
        h.update(b"\n")
    return h.hexdigest()
