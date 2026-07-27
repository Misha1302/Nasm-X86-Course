section .data
    fmtOut db "%u", 10, 0
    a dd 13
    b dd 12
    c dd 11
    d dd 10

section .text
    extern printf
    global main

main:
    push ebp
    mov ebp, esp
    and esp, -16
    mov eax, [a]
    and eax, 255

    mov ecx, [b]
    and ecx, 255
    shl ecx, 8
    or eax, ecx

    mov ecx, [c]
    and ecx, 255
    shl ecx, 16
    or eax, ecx

    mov ecx, [d]
    and ecx, 255
    shl ecx, 24
    or eax, ecx

    sub esp, 8       ; padding: 8 + 8 argument bytes = 16
    push eax
    push fmtOut
    call printf
    add esp, 16

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
