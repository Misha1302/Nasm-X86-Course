; BLOCK: RUN
section .data
    fmtOut db "%d", 10, 0
    month dd 4
    day dd 1

section .text
    extern printf
    global main

main:
    push ebp
    mov ebp, esp
    and esp, -16
    mov eax, [month]
    sub eax, 1

    mov ecx, eax
    imul eax, 41
    shr ecx, 1
    add eax, ecx
    add eax, [day]

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
