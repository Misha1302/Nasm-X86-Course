# REPAIR REPORT

## Verdict policy

```text
GO_FOR_REVIEW only when every required GitHub Actions check attached to the current PR head is successful.
Any changed head without a complete green check set is NO-GO.
```

This report deliberately does not embed a mutable commit SHA or historical workflow run IDs. The authoritative revision identity is the current head of pull request #11; the checks attached to that exact head are the release gate.

## Baseline and mutation boundary

- Repository: `Misha1302/Nasm-X86-Course`.
- Baseline branch: `main`.
- Reviewed baseline SHA: `d3a172f12d7a1f7e456a6a930007711a55d8d93c`.
- Repair branch: `repair/nasm-course-complete-20260803`.
- Pull request: `#11` into `main`.
- Merge to `main`: not authorized and not performed by this repair.

## Canonical owners

| Contract | Canonical owner |
|---|---|
| assessment/tasks/skills/evidence | `scripts/assessment_contract.json` |
| pedagogy stage sources | `scripts/pedagogy_contract.json` |
| executable ASM classes and exact outcomes | `scripts/executable_contract.json` |
| mutation cases | `scripts/mutation_contract.json` |
| generated-course source list | `scripts/course_manifest.py` |
| answer fingerprints | `scripts/answer_fingerprints.json` |

## Implemented hardening

1. Assessment proof derives every score domain from each task's actual `maximum`; no hard-coded `0..2` domain remains.
2. Duplicate evidence and asymmetric `task.skills ↔ skill.acceptable_evidence` mappings are rejected.
3. Closed-book leakage is checked against browser-visible text after HTML comments, tags, entities and Markdown presentation syntax are normalized.
4. The HTML-comment answer-splitting attack is a required mutation case.
5. Pedagogy ordering is computed from actual source paths and anchor line positions, with required content checked inside the exact declared section.
6. Mutation evidence is always regenerated from a canonical 26-case contract. Stale reports are deleted before adversarial verification.
7. A dedicated regression replaces the mutation runner with a no-op and verifies that adversarial review fails closed.
8. Generated-document provenance is content-addressed; it no longer embeds the checkout/merge commit SHA.
9. `examples/14_scanf_call.asm` is an executable RUN fixture. It enters with `esp%16=12`, reserves 4 bytes, calls `scanf` with `esp%16=0`, cleans 12 bytes and returns the read value.
10. Negative ASM fixtures require an exact supported outcome (`SIGFPE`); generic nonzero exit is not accepted.
11. Every RUN/NEGATIVE example has a bounded timeout.
12. Permanent CI renders nine decision-critical VitePress pages at desktop, mobile and 200% zoom, and fails on overflow, missing content, console errors, page errors or failed requests.
13. Tracked proof reports are regenerated and compared with Git before the contract job can pass.

## Deterministic local verification

Commands executed from the repaired source tree:

```bash
python3 scripts/generate_course_docs.py
python3 scripts/run_course_validation.py validate
python3 scripts/run_course_validation.py pedagogy
python3 scripts/validate_assessment.py
python3 scripts/run_mutations.py
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
CHECKPOINT_EXHAUSTIVE=PASS
  CP1=729
  CP2=19683
  CP3=729
  CP4=243
  CP5=6561
  CP6=243
  total=28188
FINAL_CONSTRAINT_PROOF=PASS checked=17
SCORING_REGRESSIONS=PASS count=16
MUTATIONS_TOTAL=26
MUTATIONS_CAUGHT=26
MUTATION_SUITE=PASS
ADVERSARIAL_MANDATORY_SKILL_ATTACKS=56
ADVERSARIAL_MUTATION_SURVIVORS=0
ADVERSARIAL_COMPETING_OWNER=NONE
ADVERSARIAL_REVIEW=PASS
EVIDENCE_NOOP_ATTACK=BLOCKED
```

Content-addressed receipts from this source state:

```text
GENERATED_SOURCE_TREE_SHA256=e271d0b2ebc8fd1504c9cacc73d4e7a4b0113b633ed7b2ad4cc1a6c73b23f49e
ASSESSMENT_SOURCE_DIGEST=2e07ee936052ff83b3cba14f5d31950cad87c0e6de3887c6cebe687b49eb3864
MUTATION_SOURCE_DIGEST=c0ddf7966cdc896f1db003fdc0b58100d34b17fd9e27ce059d7590a63a20b51c
ADVERSARIAL_SOURCE_DIGEST=075e98888e1eb9b797d6afa567ca0977484d73833a102a5c2b85daf78cbeac18
```

## Environment boundary

The local environment could not complete `npm ci` because its internal npm proxy returned `404` for `zwitch@2.0.4`. This is not treated as a project PASS. VitePress, Playwright and IA-32/NASM are therefore required to pass on GitHub Actions for the exact final PR head before the PR can return to Ready for review.

## Required current-head GitHub checks

```text
Audit course quality
Validate course
Course contracts / fast-contracts
Course contracts / mutation
Course contracts / docs-asm-visual
```

The browser job must upload `vitepress-render-evidence`; the artifact must contain 27 cases and zero failures.

## Release boundary

This repair may update the dedicated PR branch and review metadata. It does not authorize merge, release, deployment or modification of `main`.
