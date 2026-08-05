; BLOCK: RUN
section .data
    fmtOut db "%d %d", 10, 0
    x dd -17
    y dd 5

section .text
    extern printf
    global main

main:
    push ebp
    mov ebp, esp
    and esp, -16
    mov eax, [x]
    cdq
    idiv dword [y]

    sub esp, 4       ; padding: 4 + 12 argument bytes = 16
    push edx
    push eax
    push fmtOut
    call printf
    add esp, 16

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
