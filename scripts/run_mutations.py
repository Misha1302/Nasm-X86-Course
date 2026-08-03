from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from verification_provenance import provenance, verification_source_digest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
CONTRACT_PATH = ROOT / "scripts/mutation_contract.json"


def load_mutations(root: Path = ROOT) -> list[dict[str, str]]:
    contract = json.loads((root / "scripts/mutation_contract.json").read_text(encoding="utf-8"))
    if contract.get("schema_version") != "1.0":
        raise RuntimeError("MUTATION-CONTRACT-SCHEMA: expected 1.0")
    mutations = contract.get("mutations")
    if not isinstance(mutations, list) or not mutations:
        raise RuntimeError("MUTATION-CONTRACT-EMPTY")
    ids = [item.get("id") for item in mutations]
    if len(ids) != len(set(ids)):
        raise RuntimeError("MUTATION-CONTRACT-DUPLICATE-ID")
    required = {"id", "path", "old", "new", "owner", "expected_diagnostic"}
    for item in mutations:
        if set(item) != required:
            raise RuntimeError(f"MUTATION-CONTRACT-FIELDS {item.get('id')}: {sorted(item)}")
        if item["owner"] not in {"assessment", "semantics"}:
            raise RuntimeError(f"MUTATION-CONTRACT-OWNER {item['id']}: {item['owner']}")
    return mutations


def run_owner(root: Path, owner: str) -> subprocess.CompletedProcess[str]:
    script = "validate_assessment.py" if owner == "assessment" else "validate_semantics.py"
    return subprocess.run(
        [PYTHON, str(root / "scripts" / script)],
        cwd=root,
        text=True,
        capture_output=True,
    )


def main() -> int:
    mutations = load_mutations()
    source_digest = verification_source_digest(ROOT)
    rows: list[dict[str, object]] = []
    for item in mutations:
        mid = item["id"]
        rel = item["path"]
        old = item["old"]
        new = item["new"]
        owner = item["owner"]
        expected = item["expected_diagnostic"]
        with tempfile.TemporaryDirectory(prefix="nasm-mutation-") as td:
            dst = Path(td) / "repo"
            shutil.copytree(
                ROOT,
                dst,
                ignore=shutil.ignore_patterns(
                    "node_modules",
                    ".git",
                    "MUTATION_REPORT.*",
                    "ASSESSMENT_PROOF.json",
                    "ADVERSARIAL_REVIEW.*",
                    "render-evidence",
                    "__pycache__",
                ),
            )
            path = dst / rel
            text = path.read_text(encoding="utf-8")
            if old not in text:
                rows.append(
                    {
                        "id": mid,
                        "owner": owner,
                        "target": rel,
                        "expected": expected,
                        "exit_code": 99,
                        "message": "mutation source fragment not found",
                        "pass": False,
                    }
                )
                continue
            before = hashlib.sha256(text.encode()).hexdigest()
            mutated = text.replace(old, new, 1)
            after = hashlib.sha256(mutated.encode()).hexdigest()
            path.write_text(mutated, encoding="utf-8")
            completed = run_owner(dst, owner)
            output = (completed.stdout + "\n" + completed.stderr).strip()
            caught = completed.returncode != 0 and expected in output
            rows.append(
                {
                    "id": mid,
                    "owner": owner,
                    "target": rel,
                    "before_sha256": before,
                    "after_sha256": after,
                    "expected": expected,
                    "exit_code": completed.returncode,
                    "message": output[-1200:],
                    "pass": caught,
                }
            )

    failed = [row for row in rows if not row["pass"]]
    report = {
        "schema_version": "2.0",
        "result": "PASS" if not failed else "FAIL",
        "provenance": provenance(ROOT, Path(__file__).resolve()),
        "source_tree_sha256": source_digest,
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "mutation_ids": [item["id"] for item in mutations],
        "summary": {
            "total": len(rows),
            "caught": len(rows) - len(failed),
            "survivors": len(failed),
        },
        "results": rows,
    }
    (ROOT / "MUTATION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Mutation report",
        "",
        f"Source tree: `{source_digest}`",
        f"Mutation contract: `{report['contract_sha256']}`",
        "",
        "| ID | Owner | Expected diagnostic | Exit | Result |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['owner']} | `{row['expected']}` | "
            f"{row['exit_code']} | {'PASS' if row['pass'] else 'FAIL'} |"
        )
    lines += ["", "## Diagnostics"]
    for row in rows:
        lines += ["", f"### {row['id']}", "```text", str(row["message"]), "```"]
    (ROOT / "MUTATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"MUTATIONS_TOTAL={len(rows)}")
    print(f"MUTATIONS_CAUGHT={len(rows) - len(failed)}")
    if failed:
        for row in failed:
            print(f"MUTATION_FAIL {row['id']}: {row['message']}", file=sys.stderr)
        return 1
    print("MUTATION_SUITE=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
