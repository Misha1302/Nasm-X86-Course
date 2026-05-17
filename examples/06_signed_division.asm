section .data
    fmtOut db "%d %d", 10, 0
    x dd -17
    y dd 5

section .text
    extern printf
    global main

main:
    mov eax, [x]
    cdq
    idiv dword [y]

    push edx
    push eax
    push fmtOut
    call printf
    add esp, 12

    xor eax, eax
    ret
