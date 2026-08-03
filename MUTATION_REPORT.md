# Mutation report

| ID | Owner | Expected diagnostic | Exit | Result |
|---|---|---|---:|---|
| M01-cleanup-16-to-8 | semantics | `ASM-CALL-AREA` | 1 | PASS |
| M02-remove-padding | semantics | `ASM-CALL-AREA` | 1 | PASS |
| M03-remove-cdq | semantics | `ASM-IDIV-CDQ` | 1 | PASS |
| M04-reverse-fsubp | semantics | `ASM-X87-SUB` | 1 | PASS |
| M05-reverse-fdivp | semantics | `ASM-X87-DIV` | 1 | PASS |
| M06-remove-restore-esi | semantics | `ASM-CALLEE-SAVED` | 1 | PASS |
| M07-scanf-value | semantics | `ASM-SCANF-ADDRESS` | 1 | PASS |
| M08-idiv-immediate | semantics | `ASM-IDIV-OPERAND` | 1 | PASS |
| M09-make-10F-core | assessment | `ASSESS-DAY10-BONUS` | 1 | PASS |
| M10-include-01-16-in-100 | assessment | `ASSESS-BONUS` | 1 | PASS |
| M11-remove-cp3-loop-evidence | assessment | `ASSESS-TASK-SKILL` | 1 | PASS |
| M12-safety-optional | assessment | `ASSESS-MANDATORY` | 1 | PASS |
| M13-remove-refreshers-manifest | semantics | `MANIFEST-STANDALONE` | 1 | PASS |
| M14-answer-in-closed-book | semantics | `LEAK-C3` | 1 | PASS |
| M15-transfer-without-key | semantics | `TRANSFER-SYNC` | 1 | PASS |
| M16-change-cp-threshold | semantics | `DOCS-ASSESSMENT` | 1 | PASS |
| M17-break-anchor | semantics | `LINK-ANCHOR` | 1 | PASS |
| M18-reverse-startup | semantics | `STARTUP-DIRECTION` | 1 | PASS |
| M19-return-c3-to-day25 | semantics | `LEAK-C3` | 1 | PASS |
| M20-accept-known-false-pass | assessment | `ASSESS-REGRESSION` | 1 | PASS |

## Diagnostics

### M01-cleanup-16-to-8
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-CALL-AREA: scanf padding/cleanup mismatch
```

### M02-remove-padding
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-CALL-AREA: scanf padding/cleanup mismatch
```

### M03-remove-cdq
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-IDIV-CDQ: signed division fixture lost cdq
```

### M04-reverse-fsubp
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-X87-SUB: wrong fsubp direction
```

### M05-reverse-fdivp
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-X87-DIV: wrong fdivp direction
```

### M06-remove-restore-esi
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-CALLEE-SAVED: esi is not restored on every return path
```

### M07-scanf-value
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-SCANF-ADDRESS: scanf must receive x address, not [x] value
```

### M08-idiv-immediate
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-IDIV-OPERAND: idiv must use r/m operand, not immediate
```

### M09-make-10F-core
```text
ASSESS-DAY10-BONUS: 10F must remain optional
```

### M10-include-01-16-in-100
```text
ASSESS-BONUS: bonus tasks must not be included in the final maximum
```

### M11-remove-cp3-loop-evidence
```text
ASSESS-TASK-SKILL CP3/CP3-LOOP: mapped skill loop_lowering does not accept evidence from this task
```

### M12-safety-optional
```text
ASSESS-MANDATORY CP5/memory_safety_boundaries: outcome is no longer mandatory
```

### M13-remove-refreshers-manifest
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS
VALIDATE_ASM=PASS

MANIFEST-STANDALONE: prerequisite refreshers/final route missing
```

### M14-answer-in-closed-book
```text
LEAK-C3: docs/closed_book_workbook.md contains protected fingerprint C3-aligned-sum-call: sub esp, 8; push dword [b]; push dword [a]; call sum; add esp, 16
```

### M15-transfer-without-key
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS

TRANSFER-SYNC TR-05: task changed without contract update
```

### M16-change-cp-threshold
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS
VALIDATE_ASM=PASS
VALIDATE_MANIFEST=PASS

DOCS-ASSESSMENT: day_25 missing synchronized marker **81**
```

### M17-break-anchor
```text
VALIDATE_LEAKAGE=PASS

LINK-ANCHOR: pedagogy source docs/day_10_learning_path.md#10b-safe-ceil-machine-model missing
```

### M18-reverse-startup
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS
VALIDATE_ASM=PASS
VALIDATE_MANIFEST=PASS
VALIDATE_DOCS_CONTRACT=PASS

STARTUP-DIRECTION: startup/runtime/main direction reversed or missing
```

### M19-return-c3-to-day25
```text
LEAK-C3: docs/day_25.md contains protected fingerprint C3-aligned-sum-call: sub esp, 8; push dword [b]; push dword [a]; call sum; add esp, 16
```

### M20-accept-known-false-pass
```text
ASSESS-REGRESSION CP2-known-false-pass-ceil-zero: expected True, got False; ('mandatory skill branchless_safe_ceil: evidence 0 < 1',)
```
