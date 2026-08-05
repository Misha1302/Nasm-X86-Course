from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_nasm_examples.sh"
CURRENT = ROOT / "scripts" / "executable_contract.json"


def run(contract: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["NASM_CONTRACT_ONLY"] = "1"
    env["NASM_EXECUTABLE_CONTRACT"] = str(contract)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def require_failure(result: subprocess.CompletedProcess[str], label: str) -> None:
    output = result.stdout + result.stderr
    if result.returncode == 0 or "ASM-CONTRACT-LOAD" not in output:
        raise RuntimeError(f"{label}: fail-open result\n{output}")


def main() -> int:
    current = run(CURRENT)
    if current.returncode != 0 or "ASM_CONTRACT_RECORDS=14" not in current.stdout:
        raise RuntimeError("current executable contract did not load exactly 14 records\n" + current.stdout + current.stderr)

    with tempfile.TemporaryDirectory(prefix="nasm-contract-loader-") as temp:
        root = Path(temp)
        require_failure(run(root / "missing.json"), "missing contract")

        invalid = root / "invalid.json"
        invalid.write_text("{not-json", encoding="utf-8")
        require_failure(run(invalid), "invalid JSON")

        empty = root / "empty.json"
        empty.write_text('{"schema_version":"2.0","blocks":{}}\n', encoding="utf-8")
        require_failure(run(empty), "empty blocks")

        coverage = json.loads(CURRENT.read_text(encoding="utf-8"))
        coverage["blocks"].pop(next(iter(coverage["blocks"])))
        mismatch = root / "mismatch.json"
        mismatch.write_text(json.dumps(coverage), encoding="utf-8")
        require_failure(run(mismatch), "coverage mismatch")

    print("ASM_CONTRACT_VALID_RECORDS=14")
    print("ASM-CONTRACT_MISSING=BLOCKED")
    print("ASM-CONTRACT_INVALID_JSON=BLOCKED")
    print("ASM_CONTRACT_EMPTY=BLOCKED")
    print("ASM-CONTRACT_COVERAGE_MISMATCH=BLOCKED")
    print("ASM_CONTRACT_LOADER=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
