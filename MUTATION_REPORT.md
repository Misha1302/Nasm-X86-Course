# Mutation report

Source tree: `75a9a06024651293c907530fbc71a087f860c902e418203f1e0c1ee0906f51d6`
Mutation contract: `0c76a1ec458ef6214df1ea7b62531381c8a232b06e116b79e3b6844ba2d5f182`

| ID | Owner | Expected diagnostic | Exit | Result |
|---|---|---|---:|---|
| M01-cleanup-12-to-8 | semantics | `ASM-CALL-AREA` | 1 | PASS |
| M02-remove-padding | semantics | `ASM-CALL-AREA` | 1 | PASS |
| M03-remove-cdq | semantics | `ASM-IDIV-CDQ` | 1 | PASS |
| M04-reverse-fsubp | semantics | `ASM-X87-SUB` | 1 | PASS |
| M05-reverse-fdivp | semantics | `ASM-X87-DIV` | 1 | PASS |
| M06-remove-restore-esi | semantics | `ASM-CALLEE-SAVED` | 1 | PASS |
| M07-scanf-value | semantics | `ASM-SCANF-ADDRESS` | 1 | PASS |
| M08-idiv-immediate | semantics | `ASM-IDIV-OPERAND` | 1 | PASS |
| M09-make-10F-core | assessment | `ASSESS-DAY10-BONUS` | 1 | PASS |
| M10-include-01-16-in-100 | assessment | `ASSESS-BONUS` | 1 | PASS |
| M11-remove-cp3-loop-evidence | assessment | `ASSESS-EVIDENCE` | 1 | PASS |
| M12-safety-optional | assessment | `ASSESS-MANDATORY` | 1 | PASS |
| M13-remove-refreshers-manifest | semantics | `MANIFEST-STANDALONE` | 1 | PASS |
| M14-answer-in-closed-book | semantics | `LEAK-C3` | 1 | PASS |
| M15-transfer-without-key | semantics | `TRANSFER-SYNC` | 1 | PASS |
| M16-change-cp-threshold | semantics | `DOCS-ASSESSMENT` | 1 | PASS |
| M17-break-anchor | semantics | `LINK-ANCHOR` | 1 | PASS |
| M18-reverse-startup | semantics | `STARTUP-DIRECTION` | 1 | PASS |
| M19-return-c3-to-day25 | semantics | `LEAK-C3` | 1 | PASS |
| M20-accept-known-false-pass | assessment | `ASSESS-REGRESSION` | 1 | PASS |
| M21-html-comment-leak | semantics | `LEAK-C3` | 1 | PASS |
| M22-duplicate-evidence | assessment | `ASSESS-EVIDENCE-DUP` | 1 | PASS |
| M23-asymmetric-evidence | assessment | `ASSESS-EVIDENCE-BIDIRECTIONAL` | 1 | PASS |
| M24-remove-negative-oracle | semantics | `ASM-NEGATIVE-CONTRACT` | 1 | PASS |
| M25-move-explanation-outside-owner | semantics | `PEDAGOGY-SECTION` | 1 | PASS |

## Diagnostics

### M01-cleanup-12-to-8
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
ASSESS-EVIDENCE-BIDIRECTIONAL CP3/loop_lowering: task.skills=['CP3-LOOP'] evidence=['CP3-TABLE']
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

### M21-html-comment-leak
```text
LEAK-C3: docs/closed_book_workbook.md contains protected fingerprint C3-aligned-sum-call: sub esp, 8; push dword [b]; push dword [a]; call sum; add esp, 16
```

### M22-duplicate-evidence
```text
ASSESS-EVIDENCE-DUP CP1/overlapping_register_trace: duplicate evidence ('CP1-REG', 1)
```

### M23-asymmetric-evidence
```text
ASSESS-EVIDENCE-BIDIRECTIONAL CP1/overlapping_register_trace: task.skills=['CP1-REG'] evidence=['CP1-SIZE-R']
```

### M24-remove-negative-oracle
```text
VALIDATE_LEAKAGE=PASS
VALIDATE_PEDAGOGY=PASS
VALIDATE_TRANSFERS=PASS

ASM-NEGATIVE-CONTRACT: examples/11_idiv_overflow_negative.asm lacks exact supported expected outcome
```

### M25-move-explanation-outside-owner
```text
VALIDATE_LEAKAGE=PASS

PEDAGOGY-SECTION branchless_safe_ceil/explanation: fragment 'mov ecx, edx' missing from docs/day_10_learning_path.md#10b-safe-ceil-machine-model
```
