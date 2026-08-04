from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "1" * 40
TESTED = "2" * 40


def run(command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False, env=env)


def main() -> int:
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_ACTIONS": "true",
            "SOURCE_HEAD_SHA": SOURCE,
            "TESTED_COMMIT_SHA": TESTED,
            "SOURCE_REPOSITORY": "Misha1302/Nasm-X86-Course",
            "GITHUB_WORKFLOW": "test",
            "GITHUB_JOB": "revision",
            "GITHUB_RUN_ID": "123",
            "GITHUB_RUN_ATTEMPT": "1",
        }
    )
    with tempfile.TemporaryDirectory(prefix="nasm-revision-") as temp:
        path = Path(temp) / "report.json"
        path.write_text('{"result":"PASS"}\n', encoding="utf-8")
        bind = run([sys.executable, "scripts/bind_evidence_revision.py", str(path)], env)
        if bind.returncode != 0:
            raise RuntimeError(bind.stdout + bind.stderr)
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["revision"]["source_head_sha"] != SOURCE or data["revision"]["tested_commit_sha"] != TESTED:
            raise RuntimeError("REVISION-BINDING: incorrect revision values")
        verify = run([sys.executable, "scripts/verify_evidence_revision.py", str(path)], env)
        if verify.returncode != 0:
            raise RuntimeError(verify.stdout + verify.stderr)
        data["revision"]["source_head_sha"] = "3" * 40
        path.write_text(json.dumps(data), encoding="utf-8")
        forged = run([sys.executable, "scripts/verify_evidence_revision.py", str(path)], env)
        if forged.returncode == 0:
            raise RuntimeError("REVISION-BINDING: forged source revision was accepted")
    print("EVIDENCE_REVISION_BINDING=PASS")
    print("EVIDENCE_REVISION_FORGERY=BLOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
