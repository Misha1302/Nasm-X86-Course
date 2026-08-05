from __future__ import annotations

import hashlib
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_operation(operation: dict[str, Any]) -> str:
    return json.dumps(operation, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_contract(root: Path = ROOT) -> dict[str, Any]:
    data = json.loads((root / "scripts" / "mutation_contract.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != "3.0" or not isinstance(data.get("cases"), list):
        raise RuntimeError("MUTATION-CONTRACT: invalid schema")
    ids = [case.get("id") for case in data["cases"]]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise RuntimeError("MUTATION-CONTRACT: duplicate or empty mutation id")
    operations = [
        (case.get("path"), canonical_operation(case.get("operation", {})))
        for case in data["cases"]
    ]
    if len(operations) != len(set(operations)):
        raise RuntimeError("MUTATION-CONTRACT-DUPLICATE: duplicate target/operation pair")
    return data


def resolve_pointer(data: Any, pointer: list[Any]) -> tuple[Any, Any]:
    if not pointer:
        raise RuntimeError("MUTATION-POINTER: empty pointer")
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
        parent, key = resolve_pointer(data, operation["pointer"])
        parent[key] = operation["value"]
    elif kind == "json_delete":
        parent, key = resolve_pointer(data, operation["pointer"])
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
    elif kind == "json_add_orphan_declared_outcome":
        data["declared_outcomes"][operation["name"]] = {
            "mandatory": True,
            "owner_assessment": operation["owner_assessment"],
        }
    else:
        raise RuntimeError(f"unsupported mutation operation: {kind}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def owner_command(root: Path, case: dict[str, Any]) -> list[str]:
    owner = case["owner"]
    if owner == "assessment":
        command = [PYTHON, str(root / "scripts" / "validate_assessment.py")]
        if case["expected"] != "ASSESS-REGRESSION":
            command.append("--schema-only")
        return command
    if owner == "semantics":
        return [PYTHON, str(root / "scripts" / "validate_semantics.py")]
    raise RuntimeError(f"MUTATION-OWNER: unsupported owner {owner!r}")


def source_digest(contract: dict[str, Any], root: Path = ROOT) -> str:
    targets = [case["path"] for case in contract["cases"]]
    owners = [
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
    return digest_paths(root, [*targets, *owners])


def execute_case(case: dict[str, Any]) -> dict[str, Any]:
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
                "__pycache__",
            ),
        )
        path = destination / case["path"]
        before = sha256_file(path)
        apply_operation(path, case["operation"])
        after = sha256_file(path)
        if before == after:
            raise RuntimeError("mutation did not change target bytes")

        command = owner_command(destination, case)
        result = subprocess.run(
            command,
            cwd=destination,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        stdout = result.stdout.replace(str(destination), "<MUTATION_ROOT>")
        stderr = result.stderr.replace(str(destination), "<MUTATION_ROOT>")
        output = stdout + "\n" + stderr
        logical_command = [
            Path(command[0]).name,
            *[
                str(Path(part).relative_to(destination))
                if str(part).startswith(str(destination))
                else str(part)
                for part in command[1:]
            ],
        ]
        passed = result.returncode != 0 and case["expected"] in output
        return {
            "id": case["id"],
            "path": case["path"],
            "owner": case["owner"],
            "expected": case["expected"],
            "operation_sha256": sha256_bytes(canonical_operation(case["operation"]).encode("utf-8")),
            "target_before_sha256": before,
            "target_after_sha256": after,
            "command": logical_command,
            "exit_code": result.returncode,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
            "message": output[-3000:].strip(),
            "pass": passed,
        }


def main() -> int:
    try:
        contract = load_contract()
        rows = [execute_case(case) for case in contract["cases"]]
    except (
        RuntimeError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"MUTATION-RUNNER: {exc}", file=sys.stderr)
        return 1

    digest = source_digest(contract)
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

    lines = [
        "# Mutation report",
        "",
        f"- Source digest: `{digest}`",
        f"- Cases: **{len(rows)}**",
        "- Authority: reporting runner; merge decisions also require the independent mutation oracle.",
        "",
        "| ID | Owner | Expected diagnostic | Exit | Target changed | Result |",
        "|---|---|---|---:|---|---|",
    ]
    for row in rows:
        changed = row["target_before_sha256"] != row["target_after_sha256"]
        lines.append(
            f"| {row['id']} | {row['owner']} | `{row['expected']}` | {row['exit_code']} | "
            f"{'yes' if changed else 'no'} | {'PASS' if row['pass'] else 'FAIL'} |"
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
