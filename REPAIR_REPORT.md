# REPAIR REPORT

## Final verdict

```text
MERGED_VERIFIED
```

The NASM IA-32 course remediation was merged into `main` through pull request #11 after every required check attached to the exact source head succeeded.

## Revision identity

- Repository: `Misha1302/Nasm-X86-Course`.
- Reviewed baseline SHA: `d3a172f12d7a1f7e456a6a930007711a55d8d93c`.
- Repair branch: `repair/nasm-course-complete-20260803`.
- Source head: `2838c3eb2a231939c23ec24c7f8ba563f8d6e8b1`.
- Tested merge SHA: `9e668a32aedaa21c2df384d5a32e15a58875b6e3`.
- Final merge commit on `main`: `12c6b9cac1dc661d0c7a85582a3ee79237aa04cc`.
- Merged at: `2026-08-05T07:35:56Z`.
- Release performed: no.
- Deployment performed: no.

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

## Implemented hardening

1. Mandatory declared outcomes and executable assessment skills form an exact one-to-one topology. Orphan outcomes, missing skills, duplicate owners and `owner_assessment` drift are rejected.
2. `task.block_membership`, `block_minimums`, `score_domain` and `partial_error_rule` are mechanically cross-validated.
3. Assessment input is normalized before arithmetic. Strings, `None`, floats, booleans, negative values, out-of-range values and malformed course-level containers fail closed without exceptions or score pollution.
4. Checkpoint score domains are derived from task maxima; partial evidence is defined as `0 < score < task.maximum`.
5. The 31-case mutation policy covers outcome topology, owner drift, partial-rule drift, block membership, score domains and semantic/ASM/document contracts.
6. The reporting mutation runner is non-authoritative. An independent oracle applies each mutation, verifies the changed-file allowlist, executes the canonical owner and validates the exact diagnostic.
7. Mutation policy count and SHA-256 are locked; duplicate, replaced or weakened coverage is rejected.
8. Forged runner evidence and mutation-policy replacement attacks are regression-tested and blocked.
9. Generated proof reports are CI artifacts bound to source-head and tested-merge revisions rather than tracked mutable reports.
10. RUN/NEGATIVE ASM fixtures use bounded timeouts, exact `SIGFPE` expectations and truthful process exit statuses. Missing, malformed, empty and incomplete executable contracts fail closed.
11. The VitePress browser gate validates real production output at desktop, mobile and a 200% reflow-equivalent state. The 200% case uses a `360×450` CSS viewport, DPR `2`, `720×900` physical PNGs, active narrow responsive media queries and explicit overflow checks.

## Exact-head verification

GitHub Actions attached to source head `2838c3eb2a231939c23ec24c7f8ba563f8d6e8b1`:

| Workflow | Run | Result |
|---|---:|---|
| Audit course quality | `30985269173` | success |
| Validate course | `30985269198` | success |
| Course contracts | `30985269353` | success |

`Course contracts` included three successful jobs: `fast-contracts`, `mutation` and `docs-asm-visual`.

Observed results:

```text
ASSESSMENT_SCHEMA=PASS
ASSESSMENT_SCHEMA_PROBES=PASS count=5
CHECKPOINT_EXHAUSTIVE=PASS total=28188
FINAL_CONSTRAINT_PROOF=PASS checked=17
SCORING_REGRESSIONS=PASS count=16
ASSESSMENT_ENGINE_MALFORMED_CASES=7
ASSESSMENT_COURSE_FAIL_CLOSED=PASS
ASSESSMENT_KIND_OWNERSHIP=PASS
ASM_CONTRACT_VALID_RECORDS=14
ASM_CONTRACT_NEGATIVE_CASES=BLOCKED 4/4
ADVERSARIAL_MANDATORY_SKILL_ATTACKS=56
ADVERSARIAL_MUTATION_CASES=31
ADVERSARIAL_MUTATION_SURVIVORS=0
EVIDENCE_FORGED_RUNNER_WITH_BROKEN_OWNER=BLOCKED
EVIDENCE_MUTATION_POLICY_REPLACEMENT=BLOCKED
EVIDENCE_REVISION_BINDING=PASS
ASM_EXAMPLES_SUITE=PASS 14/14
VITEPRESS_VISUAL_CASES=27
VITEPRESS_VISUAL_SCREENSHOTS=81
VITEPRESS_VISUAL_FAILURES=0
ZOOM200_REFLOW_CASES=PASS 9/9
```

## Evidence artifacts

All artifacts below were produced by `Course contracts` run `30985269353`, identify source head `2838c3eb2a231939c23ec24c7f8ba563f8d6e8b1`, and identify tested merge SHA `9e668a32aedaa21c2df384d5a32e15a58875b6e3`.

| Artifact | ID | SHA-256 |
|---|---:|---|
| `contract-evidence` | `8921798088` | `ecaca8c0e838528668cfeae7f5b4f06dd36aaa1a92db2abdfd5ccdc639567bdc` |
| `mutation-evidence` | `8921794457` | `a5a853b112b22a2dd4925ea6917cce4077acb0b2414cce801f73a3e6fe1752c3` |
| `vitepress-render-evidence` | `8921848742` | `2948f589d5ba9fcb3a05e10515b9d5a83b32842653e329be9100bd5e491231da` |

The downloaded evidence was independently inspected after CI: all JSON reports carried the expected source/tested revision pair, all 27 visual cases passed, all 81 screenshots were present, and every 200% screenshot had physical dimensions `720×900` with no root or visible horizontal overflow.

## Final boundary

The repair and merge are complete. No release, package publication or deployment was requested or performed.
