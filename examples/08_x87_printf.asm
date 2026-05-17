section .data
    fmtOut db "%f", 10, 0
    a dd 10.0
    b dd 2.0

section .text
    extern printf
    global main

main:
    finit
    fld dword [a]
    fld dword [b]
    fdivp st1, st0

    sub esp, 8
    fstp qword [esp]
    push fmtOut
    call printf
    add esp, 12

    xor eax, eax
    ret
