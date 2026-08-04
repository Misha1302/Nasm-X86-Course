from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify revision bindings in generated JSON evidence.")
    parser.add_argument("paths", nargs="+")
    ns = parser.parse_args()

    expected_source = os.environ.get("SOURCE_HEAD_SHA") or os.environ.get("GITHUB_HEAD_SHA") or os.environ.get("GITHUB_SHA")
    expected_tested = os.environ.get("TESTED_COMMIT_SHA") or os.environ.get("GITHUB_SHA") or expected_source
    if not expected_source or not expected_tested:
        print("EVIDENCE-REVISION: expected revision environment is missing", file=sys.stderr)
        return 1
    if not SHA_RE.fullmatch(expected_source) or not SHA_RE.fullmatch(expected_tested):
        print("EVIDENCE-REVISION: expected revisions are not full commit SHAs", file=sys.stderr)
        return 1

    for raw_path in ns.paths:
        path = Path(raw_path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"EVIDENCE-REVISION: cannot read {path}: {exc}", file=sys.stderr)
            return 1
        revision = data.get("revision")
        if not isinstance(revision, dict):
            print(f"EVIDENCE-REVISION: {path} has no revision object", file=sys.stderr)
            return 1
        if revision.get("source_head_sha") != expected_source:
            print(
                f"EVIDENCE-REVISION: {path} source {revision.get('source_head_sha')!r} != {expected_source}",
                file=sys.stderr,
            )
            return 1
        if revision.get("tested_commit_sha") != expected_tested:
            print(
                f"EVIDENCE-REVISION: {path} tested {revision.get('tested_commit_sha')!r} != {expected_tested}",
                file=sys.stderr,
            )
            return 1
        print(f"EVIDENCE_REVISION_VERIFIED={path}")
    print(f"EVIDENCE_SOURCE_HEAD_SHA={expected_source}")
    print(f"EVIDENCE_TESTED_COMMIT_SHA={expected_tested}")
    print("EVIDENCE_REVISION_RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
