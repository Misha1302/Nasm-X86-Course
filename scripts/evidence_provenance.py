from __future__ import annotations

import hashlib
import os
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


def revision_metadata() -> dict[str, str]:
    source_head = (
        os.environ.get("SOURCE_HEAD_SHA")
        or os.environ.get("GITHUB_HEAD_SHA")
        or os.environ.get("GITHUB_SHA")
        or "LOCAL_UNBOUND"
    )
    tested_commit = os.environ.get("TESTED_COMMIT_SHA") or os.environ.get("GITHUB_SHA") or source_head
    return {
        "repository": os.environ.get("SOURCE_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY") or "LOCAL_UNBOUND",
        "source_head_sha": source_head,
        "tested_commit_sha": tested_commit,
        "workflow": os.environ.get("GITHUB_WORKFLOW", "LOCAL_UNBOUND"),
        "job": os.environ.get("GITHUB_JOB", "LOCAL_UNBOUND"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL_UNBOUND"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "LOCAL_UNBOUND"),
    }
