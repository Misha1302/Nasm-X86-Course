section .data
    fmtOut db "%f", 10, 0
    a dd 10.0
    b dd 2.0

section .text
    extern printf
    global main

main:
    push ebp
    mov ebp, esp
    and esp, -16
    finit
    fld dword [a]
    fld dword [b]
    fdivp st1, st0

    sub esp, 12      ; 4 bytes padding + 8-byte double
    fstp qword [esp]
    push fmtOut
    call printf
    add esp, 16

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
