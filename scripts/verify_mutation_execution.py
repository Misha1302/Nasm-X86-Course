from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
EXPECTED_CASE_COUNT = 31
EXPECTED_POLICY_SHA256 = "44fe038fabd2a071a2186c7346eb625d9e6768fe17fed81b2e4f29135b85ecdc"


class OracleError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OracleError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_and_lock_policy(root: Path) -> dict[str, Any]:
    contract = json.loads((root / "scripts" / "mutation_contract.json").read_text(encoding="utf-8"))
    require(contract.get("schema_version") == "3.0", "MUTATION-ORACLE-SCHEMA: expected 3.0")
    cases = contract.get("cases")
    require(isinstance(cases, list), "MUTATION-ORACLE-SCHEMA: cases missing")
    require(len(cases) == EXPECTED_CASE_COUNT, f"MUTATION-ORACLE-COUNT: {len(cases)} != {EXPECTED_CASE_COUNT}")
    policy_digest = sha256_bytes(canonical_json(cases))
    require(
        policy_digest == EXPECTED_POLICY_SHA256,
        f"MUTATION-ORACLE-POLICY: {policy_digest} != {EXPECTED_POLICY_SHA256}",
    )
    ids = [case.get("id") for case in cases]
    require(len(ids) == len(set(ids)) and all(ids), "MUTATION-ORACLE-IDS: duplicate or empty id")
    signatures = [
        (case.get("path"), sha256_bytes(canonical_json(case.get("operation"))))
        for case in cases
    ]
    require(
        len(signatures) == len(set(signatures)),
        "MUTATION-ORACLE-DUPLICATE: duplicate target/operation coverage",
    )
    return contract


def resolve_pointer(data: Any, pointer: list[Any]) -> tuple[Any, Any]:
    require(bool(pointer), "MUTATION-ORACLE-POINTER: empty pointer")
    current = data
    for part in pointer[:-1]:
        current = current[part]
    return current, pointer[-1]


def apply_operation_independently(path: Path, operation: dict[str, Any]) -> None:
    kind = operation["kind"]
    if kind == "text_replace":
        text = path.read_text(encoding="utf-8")
        old = operation["old"]
        require(old in text, "MUTATION-ORACLE-SOURCE: text fragment not found")
        replaced = text.replace(old, operation["new"], 1)
        require(replaced != text, "MUTATION-ORACLE-NOOP: replacement did not change text")
        path.write_text(replaced, encoding="utf-8")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    if kind == "json_set":
        parent, key = resolve_pointer(data, operation["pointer"])
        before = parent[key]
        parent[key] = operation["value"]
        require(before != parent[key], "MUTATION-ORACLE-NOOP: json_set kept the same value")
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
        name = operation["name"]
        require(name not in data["declared_outcomes"], "MUTATION-ORACLE-NOOP: orphan outcome already exists")
        data["declared_outcomes"][name] = {
            "mandatory": True,
            "owner_assessment": operation["owner_assessment"],
        }
    else:
        raise OracleError(f"MUTATION-ORACLE-OPERATION: unsupported kind {kind!r}")
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
    raise OracleError(f"MUTATION-ORACLE-OWNER: unsupported owner {owner!r}")


def snapshot(paths: set[str], root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in sorted(paths):
        path = root / relative
        require(path.is_file(), f"MUTATION-ORACLE-MISSING: {relative}")
        result[relative] = sha256_file(path)
    return result


def execute_case(case: dict[str, Any], protected_paths: set[str]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="nasm-mutation-oracle-") as temp:
        destination = Path(temp) / "repo"
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
        before = snapshot(protected_paths, destination)
        target = destination / case["path"]
        apply_operation_independently(target, case["operation"])
        after = snapshot(protected_paths, destination)
        changed = sorted(path for path in protected_paths if before[path] != after[path])
        require(
            changed == [case["path"]],
            f"MUTATION-ORACLE-ALLOWLIST {case['id']}: changed {changed}, expected {[case['path']]}",
        )

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
        require(result.returncode != 0, f"MUTATION-ORACLE-SURVIVED {case['id']}: owner exited 0")
        require(
            case["expected"] in output,
            f"MUTATION-ORACLE-DIAGNOSTIC {case['id']}: expected {case['expected']!r}; got {output[-1500:]}",
        )
        return {
            "id": case["id"],
            "path": case["path"],
            "owner": case["owner"],
            "expected": case["expected"],
            "target_before_sha256": before[case["path"]],
            "target_after_sha256": after[case["path"]],
            "exit_code": result.returncode,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
            "result": "BLOCKED",
        }


def main() -> int:
    try:
        contract = load_and_lock_policy(ROOT)
        protected_paths = {case["path"] for case in contract["cases"]}
        protected_paths.update(
            {
                "scripts/assessment_engine.py",
                "scripts/validate_assessment.py",
                "scripts/assessment_schema.py",
                "scripts/validate_semantics.py",
                "scripts/content_normalization.py",
                "scripts/evidence_provenance.py",
            }
        )
        rows = []
        for index, case in enumerate(contract["cases"], start=1):
            print(f"MUTATION_ORACLE_CASE_START={index}/{len(contract['cases'])} {case['id']}", flush=True)
            rows.append(execute_case(case, protected_paths))
    except (
        OracleError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    report = {
        "schema_version": "1.0",
        "policy_sha256": EXPECTED_POLICY_SHA256,
        "cases": rows,
        "result": "PASS",
    }
    (ROOT / "MUTATION_ORACLE.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"MUTATION_ORACLE_POLICY_SHA256={EXPECTED_POLICY_SHA256}")
    print(f"MUTATION_ORACLE_CASES={len(rows)}")
    print("MUTATION_ORACLE_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
