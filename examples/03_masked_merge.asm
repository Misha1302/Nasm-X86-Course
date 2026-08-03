; BLOCK: RUN
section .data
    fmtOut db "%u", 10, 0
    a dd 0xAAAAAAAA
    b dd 0x55555555
    c dd 0xFFFF0000

section .text
    extern printf
    global main

main:
    push ebp
    mov ebp, esp
    and esp, -16
    mov eax, [a]
    and eax, [c]

    mov ecx, [c]
    not ecx
    and ecx, [b]

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
