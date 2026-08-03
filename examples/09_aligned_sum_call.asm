; BLOCK: RUN
section .data
    fmt db "%d", 10, 0

section .text
    extern printf
    global main

sum:
    push ebp
    mov ebp, esp
    mov eax, [ebp+8]
    add eax, [ebp+12]
    mov esp, ebp
    pop ebp
    ret

main:
    push ebp
    mov ebp, esp
    and esp, -16

    ; Before preparation esp % 16 == 0.
    sub esp, 8
    push dword 20
    push dword 10
    call sum
    add esp, 16

    sub esp, 8
    push eax
    push fmt
    call printf
    add esp, 16

    mov esp, ebp
    pop ebp
    xor eax, eax
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
