from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from evidence_provenance import digest_paths

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
CONTRACT_PATH = ROOT / "scripts" / "mutation_contract.json"


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    data = json.loads((root / "scripts" / "mutation_contract.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != "2.0" or not isinstance(data.get("cases"), list):
        raise RuntimeError("MUTATION-CONTRACT: invalid schema")
    ids = [case.get("id") for case in data["cases"]]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise RuntimeError("MUTATION-CONTRACT: duplicate or empty mutation id")
    return data


def _resolve_pointer(data: Any, pointer: list[Any]) -> tuple[Any, Any]:
    current = data
    for part in pointer[:-1]:
        current = current[part]
    return current, pointer[-1]


def apply_operation(path: Path, operation: dict[str, Any]) -> None:
    kind = operation["kind"]
    if kind == "text_replace":
        text = path.read_text(encoding="utf-8")
        old = operation["old"]
        if old not in text:
            raise RuntimeError("mutation source fragment not found")
        path.write_text(text.replace(old, operation["new"], 1), encoding="utf-8")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    if kind == "json_set":
        parent, key = _resolve_pointer(data, operation["pointer"])
        parent[key] = operation["value"]
    elif kind == "json_delete":
        parent, key = _resolve_pointer(data, operation["pointer"])
        del parent[key]
    elif kind == "json_duplicate_first_evidence":
        skill = data["assessments"][operation["assessment"]]["skills"][operation["skill"]]
        skill["acceptable_evidence"].append(dict(skill["acceptable_evidence"][0]))
        skill["minimum_evidence"] = max(2, skill["minimum_evidence"])
    elif kind == "json_add_asymmetric_evidence":
        skill = data["assessments"][operation["assessment"]]["skills"][operation["skill"]]
        skill["acceptable_evidence"].append(
            {"task": operation["task"], "minimum_score": operation["minimum_score"]}
        )
    else:
        raise RuntimeError(f"unsupported mutation operation: {kind}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_owner(root: Path, owner: str) -> subprocess.CompletedProcess[str]:
    script = "validate_assessment.py" if owner == "assessment" else "validate_semantics.py"
    return subprocess.run(
        [PYTHON, str(root / "scripts" / script)],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def source_digest(contract: dict[str, Any], root: Path = ROOT) -> str:
    targets = [case["path"] for case in contract["cases"]]
    owners = [
        "scripts/mutation_contract.json",
        "scripts/run_mutations.py",
        "scripts/validate_semantics.py",
        "scripts/validate_assessment.py",
        "scripts/assessment_engine.py",
        "scripts/content_normalization.py",
        "scripts/evidence_provenance.py",
    ]
    return digest_paths(root, [*targets, *owners])


def main() -> int:
    try:
        contract = load_contract()
    except (RuntimeError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    rows: list[dict[str, Any]] = []
    for case in contract["cases"]:
        with tempfile.TemporaryDirectory(prefix="nasm-mutation-") as temp:
            destination = Path(temp) / "repo"
            shutil.copytree(
                ROOT,
                destination,
                ignore=shutil.ignore_patterns(
                    "node_modules",
                    ".git",
                    "MUTATION_REPORT.*",
                    "ASSESSMENT_PROOF.json",
                    "ADVERSARIAL_REVIEW.*",
                    "render-evidence",
                    ".vitepress",
                ),
            )
            path = destination / case["path"]
            try:
                apply_operation(path, case["operation"])
                result = run_owner(destination, case["owner"])
                output = (result.stdout + "\n" + result.stderr).strip()
                passed = result.returncode != 0 and case["expected"] in output
                message = output[-2000:]
                exit_code = result.returncode
            except (RuntimeError, KeyError, TypeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
                passed = False
                message = str(exc)
                exit_code = 99
            rows.append(
                {
                    "id": case["id"],
                    "path": case["path"],
                    "owner": case["owner"],
                    "expected": case["expected"],
                    "exit_code": exit_code,
                    "message": message,
                    "pass": passed,
                }
            )

    digest = source_digest(contract)
    report = {
        "schema_version": "2.0",
        "source_digest": digest,
        "mutation_contract_digest": digest_paths(ROOT, ["scripts/mutation_contract.json"]),
        "cases": rows,
    }
    (ROOT / "MUTATION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Mutation report",
        "",
        f"- Source digest: `{digest}`",
        f"- Cases: **{len(rows)}**",
        "",
        "| ID | Owner | Expected diagnostic | Exit | Result |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['owner']} | `{row['expected']}` | {row['exit_code']} | "
            f"{'PASS' if row['pass'] else 'FAIL'} |"
        )
    lines += ["", "## Diagnostics"]
    for row in rows:
        lines += ["", f"### {row['id']}", "```text", row["message"], "```"]
    (ROOT / "MUTATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    failed = [row for row in rows if not row["pass"]]
    print(f"MUTATION_SOURCE_DIGEST={digest}")
    print(f"MUTATIONS_TOTAL={len(rows)}")
    print(f"MUTATIONS_CAUGHT={len(rows) - len(failed)}")
    if failed:
        for row in failed:
            print(f"MUTATION_FAIL {row['id']}: {row['message']}", file=sys.stderr)
        return 1
    print("MUTATION_SUITE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
