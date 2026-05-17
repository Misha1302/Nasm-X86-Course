section .data
    fmtOut db "%d", 10, 0
    x dd -123

section .text
    extern printf
    global main

main:
    mov eax, [x]
    mov edx, eax
    sar edx, 31
    xor eax, edx
    sub eax, edx

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
