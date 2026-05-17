section .data
    fmtOut db "%d", 10, 0
    month dd 4
    day dd 1

section .text
    extern printf
    global main

main:
    mov eax, [month]
    sub eax, 1

    mov ecx, eax
    imul eax, 41
    shr ecx, 1
    add eax, ecx
    add eax, [day]

    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
