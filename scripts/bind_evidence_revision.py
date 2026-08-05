from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from evidence_provenance import revision_metadata

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind generated JSON evidence to the tested GitHub revision.")
    parser.add_argument("paths", nargs="+")
    ns = parser.parse_args()

    revision = revision_metadata()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for key in ("source_head_sha", "tested_commit_sha"):
            value = revision[key]
            if not SHA_RE.fullmatch(value):
                print(f"EVIDENCE-REVISION: {key} is not a full commit SHA: {value!r}", file=sys.stderr)
                return 1

    for raw_path in ns.paths:
        path = Path(raw_path)
        if not path.is_file():
            print(f"EVIDENCE-REVISION: missing report {path}", file=sys.stderr)
            return 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"EVIDENCE-REVISION: cannot read {path}: {exc}", file=sys.stderr)
            return 1
        if not isinstance(data, dict):
            print(f"EVIDENCE-REVISION: {path} root must be an object", file=sys.stderr)
            return 1
        data["revision"] = revision
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"EVIDENCE_REVISION_BOUND={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
