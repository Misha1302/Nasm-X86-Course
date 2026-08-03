# REPAIR REPORT

Generated: `2026-08-03T00:34:19Z`

## Verdict

```text
NO-GO
```

The repair implementation, semantic proof, mutation suite and degraded renderer evidence are complete inside this bundle. Release-grade acceptance is **not** granted because the complete Git checkout could not be materialized in the container, `npm ci`/VitePress could not run here, NASM is absent and the kernel cannot execute IA-32 binaries. The archive is therefore a baseline-pinned repair overlay, not a false claim that the full repository passed every Definition-of-Done item.

## Baseline

```text
branch: main (verified through the GitHub connector)
source HEAD: d3a172f12d7a1f7e456a6a930007711a55d8d93c
reviewed historical SHA: d3a172f12d7a1f7e456a6a930007711a55d8d93c
current main vs reviewed SHA: identical
repository root in this container: NOT_MATERIALIZED
upstream / staged / unstaged / untracked / merge state of real checkout: NOT_OBSERVED
publication: NOT_PERFORMED
```

Direct `git clone`, raw GitHub and codeload access failed with DNS resolution errors. The current branch and SHA were independently read through the GitHub connector. `scripts/apply_repair.py` refuses any branch other than clean pinned `main`, checks guarded Git blob identities and merge/rebase/cherry-pick state before its first mutation.

Tool versions observed:

```text
git 2.47.3
node v22.16.0
npm 10.9.2
Python 3.13.5
GCC 14.2.0
NASM NOT_FOUND
VitePress NOT_INSTALLED_IN_BUNDLE
native IA-32 execution NOT_SUPPORTED
```

## Root causes

1. **Assessment owner violation.** The previous canonical contract owned totals and marker lists but not atomic outcomes, evidence or an executable decision predicate.
2. **Admission-page boundary violation.** `day_25` duplicated answer-bearing code/formulas immediately before the closed attempt.
3. **Pedagogy dependency violation.** Day 10 assessed a machine mechanism before its explanation and required future conditional material inside a task that forbade conditional mechanisms.
4. **Transfer-contract violation.** Several TR tasks preserved the example's reasoning graph and changed only surface syntax.
5. **Executable-example ownership violation.** ASM blocks lacked explicit execution classes and several ABI/instruction boundaries had only string markers, not semantic checks.
6. **Generated-artifact provenance violation.** Closed-book generation stripped containers but did not validate normalized answer fingerprints or bind outputs to an exact source-tree digest.
7. **Mutation ownership violation.** Critical invariants had no test proving that the correct validator fails with a useful diagnostic.

## Изменения

| Requirement | Owning component | Changed files | Validation | Result |
|---|---|---|---|---|
| Atomic skill/evidence model | `scripts/assessment_contract.json` | contract, engine, fixtures | exhaustive CP + final constraint proof | PASS |
| No false PASS | `assessment_engine.py` | engine, scoring fixtures | 16 regressions, 55 adversarial skill attacks | PASS |
| No Day 25 leakage | fingerprint contract | `day_25.md`, fingerprint validator | semantic + M19 | PASS |
| Closed-book protection | full generator replacement | generator, source manifest | semantic + M14 | PASS in fixture; full generator not run in real checkout |
| Readiness composition | assessment owner | Day 25, final, keys, remediation | docs-contract validator | PASS |
| Day 10 ordering | pedagogy contract | Day 10 sections, garden, CP2 | dependency validator + six remainder oracle cases | PASS |
| Real transfer tasks | transfer owner | TR-05/16/17/19/23, keys, walkthroughs | fingerprints, structure, diagnostic counterexamples | PASS |
| Signed division overflow | instruction boundary | Day 09, reference, CP2 subpart, negative fixture | semantic + deterministic oracle + M03/M08 | PASS except native NASM run |
| Branchless abs boundary | example contract | guarded replacement of example 04 | semantic contract | PASS |
| Callee-saved all returns | semantic ASM validator | example 12, TR-17 | M06 | PASS |
| ASM block classes | executable contract | examples + classifier | complete coverage validator | PASS in overlay; full target classification occurs on apply |
| 20 mutation cases | mutation owner | `run_mutations.py` | correct owner + diagnostic | PASS 20/20 |
| CI integration | GitHub Actions workflow | `course-contracts.yml` | static inspection | IMPLEMENTED, NOT_RUN remotely |
| Safe target mutation | apply owner | `apply_repair.py`, overlay manifest | synthetic end-to-end application | PASS |
| Visual evidence | renderer harness | 9 pages × 3 viewports | 27 cases / 71 screenshots | DEGRADED PASS, not VitePress |

## Scoring proof

Known old false-PASS states now fail:

| Fixture | New result | Missing mandatory skill |
|---|---|---|
| `CP2-CEIL=0`, total 13 | FAIL | `branchless_safe_ceil` |
| `CP3-BIT=0`, total 10 | FAIL | `single_bit_test` |
| `CP5-NAN=0` | FAIL | `nan_model` |
| `CP6-THIS=0` | FAIL | `this_pointer_machine_facts` |
| `CP6-OBJECT=0` | FAIL | `object_layout_boundaries` |
| Final `E1=0` | FAIL | `memory_safety_model` |
| Final `E3=0` | FAIL | `object_model_hypothesis_boundary` |
| Final `C2=0` | FAIL | `write_cdecl_function` |
| Final `A4=0` | FAIL | `arithmetic_abs_area_boundary` |

Proof results:

```text
checkpoint exhaustive assignments:
  CP1 729
  CP2 6561
  CP3 729
  CP4 243
  CP5 6561
  CP6 243
  total 15066
final solver: monotone bounded constraint enumeration
final missing-skill witnesses: 0
positive PASS fixtures: CP1..CP6 + FINAL all pass
regression fixtures total: 16
```

`ASSESSMENT_PROOF.json` contains the machine-readable decisions.

## Mutation report

All required mutations were executed in temporary copies. Result:

```text
MUTATIONS_TOTAL=20
MUTATIONS_CAUGHT=20
MUTATION_SUITE=PASS
```

Every mutation failed at its assigned assessment/semantic owner and the expected diagnostic was observed. Full commands and messages are in `MUTATION_REPORT.md` and `MUTATION_REPORT.json`.

## Adversarial review

```text
mandatory-skill false-PASS attacks: 55 blocked
answer leakage attack: blocked
day-10 future-dependency attack: blocked
transfer copy/rename attack: blocked
mutation-evasion attempts: 20
mutation-evasion survivors: 0
competing machine-readable assessment owners: 0
```

Details: `ADVERSARIAL_REVIEW.md` and `ADVERSARIAL_REVIEW.json`.

## Exact checks

| Command | Exit | Observed result |
|---|---:|---|
| `npm ci --no-audit --no-fund` | 1 | bundle has no tracked baseline `package-lock.json`; no dependency install claimed |
| `npm run docs:generate` | 0 | four generated fixture artifacts rebuilt |
| `npm run course:validate` | 0 | leakage, pedagogy, transfer, ASM, manifest, docs and links PASS; assessment proof PASS |
| `npm run course:pedagogy` | 0 | semantic pedagogy suite PASS |
| `python3 scripts/validate_assessment.py` | 0 | exhaustive/constraint/regression proof PASS |
| `python3 scripts/run_mutations.py` | 0 | 20/20 caught |
| `python3 scripts/run_adversarial_review.py` | 0 | 55 skill attacks and all other attacks blocked |
| `npm run docs:build` | 127 | all pre-build generators/validators PASS; `vitepress: not found` |
| `bash scripts/verify_nasm_examples.sh` | 2 | `ASM-TOOL-MISSING: nasm` |
| `bash scripts/verify_environment.sh` | 0 | GNU IA-32 assemble/link PASS; semantic oracles PASS; native execution unavailable |
| `python3 scripts/render_critical_pages.py` | 0 | 27 degraded Chromium cases, 71 screenshots, no horizontal overflow/raw anchors |
| synthetic baseline-pinned apply test | 0 | protected sections preserved; classifier and mutation boundary PASS |

## Generated artifacts

| Path | Size | SHA-256 | Source revision | Included |
|---|---:|---|---|---|
| `docs/textbook.md` | 38825 | `a883a5934af0d50874362cc3c6cf8e83a25bfb578bf9ca8c469354a51b748e5c` | baseline + repair fixture | yes |
| `docs/course_migration.md` | 147 | `e6ca7ef2a45155c0ef9b787c80229b74718c6b9b552db86eaefe6ecfc15902c8` | baseline + repair fixture | yes |
| `docs/closed_book_workbook.md` | 12268 | `81c34049b1970681b955e1f8a8b78722ea5b2253451485fc12451204ea41fb44` | baseline + repair fixture | yes |
| `docs/generated_source_manifest.json` | 1602 | `41c0f29e82c736207495b2d0bd0859feb178d0669a423f2262a0eaf6be245481` | source-tree digest | yes |
| `ASSESSMENT_PROOF.json` | 4399 | `f15fdaa0eded88fad85943849ac6f74a7313b941ede4534629e5a7d108aca6ca` | repair contract | yes |
| `MUTATION_REPORT.md` | 4667 | `bb1099a14eaab8e1f1a1c3892f532532006874f09ed013d8b06d2f8de315746e` | repair contract | yes |
| `ADVERSARIAL_REVIEW.md` | 420 | `8cfcb325d618fed9bf4cc58c6d8e8237a3761a8f346cc422641d07590d0b5751` | repair contract | yes |
| `render-evidence/visual_evidence.json` | 14338 | `da8a4f91791108d1c50a2cad7ef760870d816dfd93cbe85962826214837d89ca` | degraded renderer | yes |

The final archive hash is recorded externally in the sibling receipt because embedding an archive's own final digest inside itself is self-referential.

## Независимые статусы

```text
Implementation: PASS for baseline-pinned overlay; NOT_APPLIED to real checkout
Validation: PASS for semantic, assessment, mutation and adversarial suites
Artifact: PASS after clean staging/archive verification
Environment: DEGRADED
Documentation: PASS for decision-critical repair surface
Visual: DEGRADED PASS; not a VitePress renderer
Provider AI behavior: NOT_RUN
```

## Не проверено

- Application to the complete real Git worktree at the pinned SHA.
- Real checkout `git status`, upstream and operation-state output.
- `npm ci` with the repository's tracked `package-lock.json`.
- VitePress build, preview, sidebar and actual theme rendering.
- NASM assembly/link/run of every full repository example and golden output.
- Native IA-32 negative `SIGFPE` execution in this kernel.
- GitHub Actions execution on a PR/main revision.
- Provider-backed AI tutor behavior; status remains `NOT_RUN`.
- Remote SHA after publication, because no push/publication was performed.

## Completion gap

```text
requested outcome
→ fully repaired and independently verified complete repository

observed outcome
→ baseline-pinned repair overlay
→ atomic assessment proof PASS
→ semantic suite PASS
→ mutation suite 20/20 PASS
→ adversarial skill attacks 55/55 blocked
→ degraded visual evidence PASS
→ safe synthetic application PASS

remaining gap
→ materialize the complete pinned checkout
→ apply the overlay
→ run npm ci with tracked lockfile
→ run actual VitePress build/preview
→ run NASM + GCC-multilib golden suite on native/compatible IA-32 execution
→ inspect the resulting full diff and actual VitePress pages
```
