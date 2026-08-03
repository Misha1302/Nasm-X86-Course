; BLOCK: NEGATIVE
; EXPECTED: divide exception for INT32_MIN / -1
global _start
section .text
_start:
    mov eax, 0x80000000
    cdq
    mov ecx, -1
    idiv ecx
    mov eax, 1
    xor ebx, ebx
    int 0x80
section .note.GNU-stack noalloc noexec nowrite progbits
