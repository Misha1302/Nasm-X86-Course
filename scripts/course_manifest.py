from __future__ import annotations

DAY_RELATIVE_PATHS = tuple(f"docs/day_{i:02d}.md" for i in range(1, 26))

STANDALONE_RELATIVE_PATHS = (
    "docs/prerequisites.md",
    "docs/prerequisite_refreshers.md",
    "docs/glossary.md",
    "docs/self_study.md",
    "docs/support_matrix.md",
    "docs/c_abi.md",
    "docs/patterns/libc_alignment.md",
    *DAY_RELATIVE_PATHS[:10],
    "docs/day_10_learning_path.md",
    *DAY_RELATIVE_PATHS[10:24],
    "docs/transfer_workbook.md",
    "docs/transfer_keys.md",
    "docs/transfer_walkthroughs.md",
    "docs/checkpoints.md",
    "docs/checkpoint_keys.md",
    "docs/day_25.md",
    "docs/final_exam.md",
    "docs/final_exam_keys.md",
    "docs/final_remediation.md",
    "docs/ai_tutor_prompts.md",
    "docs/ai_tutor_eval.md",
)

GENERATED_RELATIVE_PATHS = (
    "docs/textbook.md",
    "docs/course_migration.md",
    "docs/closed_book_workbook.md",
)
