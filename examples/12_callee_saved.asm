; BLOCK: COMPILE
global clamp_sum
section .text
clamp_sum:
    push ebp
    mov ebp, esp
    push esi
    mov esi, [ebp+8]
    add esi, [ebp+12]
    cmp esi, [ebp+16]
    jle .done
    mov esi, [ebp+16]
.done:
    mov eax, esi
    pop esi
    pop ebp
    ret
section .note.GNU-stack noalloc noexec nowrite progbits
