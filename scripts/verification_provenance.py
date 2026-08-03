from __future__ import annotations

from hashlib import sha256
from pathlib import Path

EXCLUDED_NAMES = {
    'ASSESSMENT_PROOF.json',
    'ADVERSARIAL_REVIEW.json',
    'ADVERSARIAL_REVIEW.md',
    'MUTATION_REPORT.json',
    'MUTATION_REPORT.md',
    'REPAIR_REPORT.md',
    'REPAIR_APPLY_RECEIPT.json',
}
EXCLUDED_PARTS = {'.git', '__pycache__', 'node_modules', 'render-evidence', 'dist', 'cache'}
EXCLUDED_GENERATED = {
    'docs/textbook.md',
    'docs/course_migration.md',
    'docs/closed_book_workbook.md',
    'docs/generated_source_manifest.json',
}
ROOTS = ('scripts', 'docs', 'examples', 'tests', 'evals')


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verification_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel_root in ROOTS:
        base = root / rel_root
        if not base.exists():
            continue
        for path in base.rglob('*'):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if path.name in EXCLUDED_NAMES or rel in EXCLUDED_GENERATED:
                continue
            if any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts):
                continue
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def verification_source_digest(root: Path) -> str:
    h = sha256()
    for path in verification_files(root):
        rel = path.relative_to(root).as_posix().encode('utf-8')
        data = path.read_bytes()
        h.update(rel + b'\0' + sha256(data).digest() + b'\n')
    return h.hexdigest()


def provenance(root: Path, runner: Path) -> dict[str, str]:
    return {
        'source_tree_sha256': verification_source_digest(root),
        'runner': runner.relative_to(root).as_posix(),
        'runner_sha256': file_sha256(runner),
    }
