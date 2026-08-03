from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nasm-evidence-integrity-") as temp:
        copy = Path(temp) / "repo"
        shutil.copytree(
            ROOT,
            copy,
            ignore=shutil.ignore_patterns(".git", "node_modules", ".vitepress", "render-evidence"),
        )
        for rel in ("MUTATION_REPORT.json", "MUTATION_REPORT.md"):
            path = copy / rel
            if path.exists():
                path.unlink()
        (copy / "scripts" / "run_mutations.py").write_text(
            "print('MUTATIONS_TOTAL=26')\nprint('MUTATION_SUITE=PASS')\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(copy / "scripts" / "run_adversarial_review.py")],
            cwd=copy,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode == 0 or "ADVERSARIAL-MUTATION-REPORT: missing fresh report" not in output:
            print(output, file=sys.stderr)
            return 1
    print("EVIDENCE_NOOP_ATTACK=BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
