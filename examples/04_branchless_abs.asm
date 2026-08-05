; BLOCK: RUN
; CONTRACT: signed abs result is valid only for x != INT32_MIN.
; For INT32_MIN the bit pattern 0x80000000 is a uint32_t magnitude, not positive int32_t.
section .data
    fmtOut db "%d", 10, 0
    x dd -123

section .text
    extern printf
    global main

main:
    push ebp
    mov ebp, esp
    and esp, -16
    mov eax, [x]
    mov edx, eax
    sar edx, 31
    xor eax, edx
    sub eax, edx

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
