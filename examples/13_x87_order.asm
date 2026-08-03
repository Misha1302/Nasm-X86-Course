; BLOCK: RUN
; CONTRACT: computes (a-b)/c with fsubp/fdivp directions checked by validator.
global expr
section .text
expr:
    fld qword [a]
    fld qword [b]
    fsubp st1, st0
    fld qword [c]
    fdivp st1, st0
    ret
section .data
a dq 10.0
b dq 4.0
c dq 3.0
section .note.GNU-stack noalloc noexec nowrite progbits
