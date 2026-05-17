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

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
