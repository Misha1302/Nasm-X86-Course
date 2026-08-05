; BLOCK: RUN
; CONTRACT: eax=a>=0, ecx=b>0; returns ceil(a/b) in eax.
global branchless_ceil
section .text
branchless_ceil:
    xor edx, edx
    div ecx
    mov ecx, edx
    neg ecx
    or ecx, edx
    shr ecx, 31
    add eax, ecx
    ret
section .note.GNU-stack noalloc noexec nowrite progbits
