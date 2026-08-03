from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nasm-meta-regression-") as td:
        dst = Path(td) / "repo"
        shutil.copytree(
            ROOT,
            dst,
            ignore=shutil.ignore_patterns(
                ".git",
                "node_modules",
                "__pycache__",
                "render-evidence",
                "MUTATION_REPORT.*",
                "ADVERSARIAL_REVIEW.*",
                "ASSESSMENT_PROOF.json",
            ),
        )
        for rel in ("MUTATION_REPORT.json", "MUTATION_REPORT.md"):
            (dst / rel).unlink(missing_ok=True)
        (dst / "scripts/run_mutations.py").write_text(
            "print('MUTATION_SUITE=PASS')\nraise SystemExit(0)\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(dst / "scripts/run_adversarial_review.py")],
            cwd=dst,
            text=True,
            capture_output=True,
        )
        output = result.stdout + result.stderr
        require(result.returncode != 0, "META-MUTATION-NOOP: adversarial gate accepted a no-op mutation runner")
        require(
            "ADVERSARIAL-MUTATION-FRESHNESS" in output,
            "META-MUTATION-NOOP: failure was not owned by freshness contract: " + output[-1000:],
        )
    print("REVIEW_REGRESSION_MUTATION_NOOP=BLOCKED")
    print("REVIEW_REGRESSIONS=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
