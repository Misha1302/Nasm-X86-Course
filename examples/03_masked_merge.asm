section .data
    fmtOut db "%u", 10, 0
    a dd 0xAAAAAAAA
    b dd 0x55555555
    c dd 0xFFFF0000

section .text
    extern printf
    global main

main:
    mov eax, [a]
    and eax, [c]

    mov ecx, [c]
    not ecx
    and ecx, [b]

    or eax, ecx

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
