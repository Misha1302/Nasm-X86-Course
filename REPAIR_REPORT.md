# REPAIR REPORT

## Verdict policy

```text
GO_FOR_REVIEW only when every required check attached to the current PR head succeeds.
Any changed head without a complete current-head check set remains NO-GO.
```

This report intentionally does not embed a mutable commit SHA or historical workflow run ID. Pull request #11 and the checks attached to its exact current head are the authoritative revision identity.

## Boundary

- Repository: `Misha1302/Nasm-X86-Course`.
- Baseline branch: `main`.
- Reviewed baseline SHA: `d3a172f12d7a1f7e456a6a930007711a55d8d93c`.
- Repair branch: `repair/nasm-course-complete-20260803`.
- Pull request: `#11` into `main`.
- Merge, release and deployment are not authorized and are not performed by this repair.

## Canonical owners

| Contract | Canonical owner |
|---|---|
| assessment/tasks/skills/evidence/outcomes | `scripts/assessment_contract.json` |
| executable assessment decision | `scripts/assessment_engine.py` |
| assessment schema and finite proof | `scripts/validate_assessment.py` |
| mutation policy | `scripts/mutation_contract.json` |
| mutation execution verdict | `scripts/verify_mutation_execution.py` |
| semantic course contracts | `scripts/validate_semantics.py` |
| executable ASM classes and outcomes | `scripts/executable_contract.json` |
| generated-course source list | `scripts/course_manifest.py` |

## Implemented professional hardening

1. Mandatory declared outcomes and executable assessment skills must be an exact one-to-one topology. Orphan outcomes, missing skills, duplicate owners and `owner_assessment` drift are rejected.
2. `task.block_membership`, `block_minimums`, `score_domain` and `partial_error_rule` are mechanically cross-validated instead of remaining decorative duplicate fields.
3. Assessment input is normalized before any arithmetic. Strings, `None`, floats, booleans, negative values, out-of-range values and non-mapping inputs fail closed without exceptions or type pollution.
4. Checkpoint score domains remain derived from each task's actual `maximum`; partial evidence is defined as `0 < score < task.maximum`.
5. The mutation policy contains 31 distinct target/operation cases, including outcome coverage, owner drift, partial-rule drift, block-membership drift and score-domain drift.
6. The reporting mutation runner is non-authoritative. A separate implementation independently applies every mutation, verifies the exact changed-file allowlist, runs the canonical owner and decides whether the expected diagnostic was observed.
7. The independent oracle locks the canonical mutation policy by count and SHA-256, rejecting replaced, duplicated or weakened coverage before execution.
8. Evidence-integrity regressions prove that a forged runner report cannot hide a broken validator and that mutation-policy replacement is rejected.
9. Generated proof reports are CI artifacts, not tracked repository state. Every workflow run regenerates revision-bearing evidence from the checked-out source.
10. RUN/NEGATIVE ASM fixtures have bounded timeouts; negative fixtures require exact `SIGFPE`; RUN diagnostics preserve the real process/timeout exit status.
11. The permanent VitePress browser gate remains responsible for real build, desktop/mobile/200% rendering, overflow, console, page and request failures.

## Deterministic local verification

Executed against the reconstructed source state corresponding to the reviewed PR head, with current files independently matched against GitHub blobs before modification:

```bash
python3 scripts/generate_course_docs.py
python3 scripts/validate_semantics.py
python3 scripts/validate_assessment.py
python3 tests/test_assessment_engine.py
python3 scripts/run_mutations.py
python3 scripts/verify_mutation_execution.py
python3 scripts/run_adversarial_review.py
python3 tests/test_evidence_integrity.py
python3 -m compileall -q scripts tests
```

Observed receipts:

```text
GENERATED_DOCS=PASS
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS
VALIDATE_ASM=PASS
VALIDATE_MANIFEST=PASS
VALIDATE_DOCS_CONTRACT=PASS
VALIDATE_LINKS=PASS
ASSESSMENT_SCHEMA=PASS
ASSESSMENT_SCHEMA_PROBES=PASS
CHECKPOINT_EXHAUSTIVE=PASS CP1:729 CP2:19683 CP3:729 CP4:243 CP5:6561 CP6:243
FINAL_CONSTRAINT_PROOF=PASS checked=17
SCORING_REGRESSIONS=PASS count=16
ASSESSMENT_ENGINE_MALFORMED_CASES=7
ASSESSMENT_ENGINE_FAIL_CLOSED=PASS
MUTATIONS_TOTAL=31
MUTATIONS_CAUGHT=31
MUTATION_SUITE=PASS
MUTATION_ORACLE_CASES=31
MUTATION_ORACLE_RESULT=PASS
ADVERSARIAL_MANDATORY_SKILL_ATTACKS=56
ADVERSARIAL_MUTATION_CASES=31
ADVERSARIAL_MUTATION_ORACLE=PASS
ADVERSARIAL_MUTATION_SURVIVORS=0
ADVERSARIAL_REVIEW=PASS
EVIDENCE_FORGED_RUNNER_WITH_BROKEN_OWNER=BLOCKED
EVIDENCE_MUTATION_POLICY_REPLACEMENT=BLOCKED
EVIDENCE_INTEGRITY=PASS
```

Canonical mutation policy SHA-256:

```text
44fe038fabd2a071a2186c7346eb625d9e6768fe17fed81b2e4f29135b85ecdc
```

## Environment boundary

NASM is unavailable in the local execution container, so no local claim is made for assembly/link/runtime acceptance. The exact current PR head must pass the permanent GitHub Actions IA-32/NASM job and real VitePress/Playwright job before the PR may return to Ready for review.

## Required current-head checks

```text
Audit course quality
Validate course
Course contracts / fast-contracts
Course contracts / mutation
Course contracts / docs-asm-visual
```

The contract jobs must upload fresh `contract-evidence` and `mutation-evidence`; the browser job must upload `vitepress-render-evidence` with 27 cases and zero failures.

## Current status

```text
PENDING_CURRENT_HEAD_CI
```
