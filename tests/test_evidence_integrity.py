from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


FAKE_RUNNER = r'''from __future__ import annotations
import json
from pathlib import Path
from evidence_provenance import digest_paths

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads((ROOT / "scripts" / "mutation_contract.json").read_text(encoding="utf-8"))
paths = [case["path"] for case in contract["cases"]]
paths += [
    "scripts/mutation_contract.json",
    "scripts/run_mutations.py",
    "scripts/verify_mutation_execution.py",
    "scripts/validate_semantics.py",
    "scripts/validate_assessment.py",
    "scripts/assessment_schema.py",
    "scripts/assessment_engine.py",
    "scripts/content_normalization.py",
    "scripts/evidence_provenance.py",
]
digest = digest_paths(ROOT, paths)
rows = [
    {
        "id": case["id"],
        "path": case["path"],
        "owner": case["owner"],
        "expected": case["expected"],
        "pass": True,
    }
    for case in contract["cases"]
]
report = {
    "schema_version": "3.0",
    "source_digest": digest,
    "mutation_contract_digest": digest_paths(ROOT, ["scripts/mutation_contract.json"]),
    "cases": rows,
}
(ROOT / "MUTATION_REPORT.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
(ROOT / "MUTATION_REPORT.md").write_text("# forged\n", encoding="utf-8")
print(f"MUTATIONS_TOTAL={len(rows)}")
print(f"MUTATIONS_CAUGHT={len(rows)}")
print("MUTATION_SUITE=PASS")
'''


def copy_repo(destination: Path) -> None:
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            "node_modules",
            ".vitepress",
            "render-evidence",
            "__pycache__",
            "ASSESSMENT_PROOF.json",
            "MUTATION_REPORT.*",
            "MUTATION_ORACLE.json",
            "ADVERSARIAL_REVIEW.*",
        ),
    )


def run(command: list[str], root: Path, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def test_forged_runner_cannot_hide_broken_owner() -> None:
    with tempfile.TemporaryDirectory(prefix="nasm-evidence-forgery-") as temp:
        copy = Path(temp) / "repo"
        copy_repo(copy)
        (copy / "scripts" / "run_mutations.py").write_text(FAKE_RUNNER, encoding="utf-8")
        (copy / "scripts" / "validate_assessment.py").write_text(
            "print('FORGED_ASSESSMENT_VALIDATOR=PASS')\n",
            encoding="utf-8",
        )
        result = run([sys.executable, str(copy / "scripts" / "run_adversarial_review.py")], copy)
        output = result.stdout + result.stderr
        if result.returncode == 0 or "ADVERSARIAL-MUTATION-ORACLE" not in output:
            raise RuntimeError("EVIDENCE-FORGERY-NOT-BLOCKED:\n" + output[-5000:])


def test_contract_replacement_is_policy_locked() -> None:
    with tempfile.TemporaryDirectory(prefix="nasm-policy-replacement-") as temp:
        copy = Path(temp) / "repo"
        copy_repo(copy)
        path = copy / "scripts" / "mutation_contract.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract["cases"][1]["operation"] = dict(contract["cases"][0]["operation"])
        path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = run([sys.executable, str(copy / "scripts" / "verify_mutation_execution.py")], copy, timeout=120)
        output = result.stdout + result.stderr
        if result.returncode == 0 or "MUTATION-ORACLE-POLICY" not in output:
            raise RuntimeError("MUTATION-POLICY-REPLACEMENT-NOT-BLOCKED:\n" + output[-3000:])


def main() -> int:
    test_forged_runner_cannot_hide_broken_owner()
    test_contract_replacement_is_policy_locked()
    print("EVIDENCE_FORGED_RUNNER_WITH_BROKEN_OWNER=BLOCKED")
    print("EVIDENCE_MUTATION_POLICY_REPLACEMENT=BLOCKED")
    print("EVIDENCE_INTEGRITY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
