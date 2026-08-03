.intel_syntax noprefix
.global _start
.section .text
nonzero_u32:
    mov ecx, edx
    neg ecx
    or ecx, edx
    shr ecx, 31
    mov eax, ecx
    ret
_start:
    lea esi, cases
    lea edi, expected
    mov ebp, 6
.loop:
    mov edx, DWORD PTR [esi]
    call nonzero_u32
    cmp eax, DWORD PTR [edi]
    jne .fail
    add esi, 4
    add edi, 4
    dec ebp
    jne .loop
    mov eax, 1
    xor ebx, ebx
    int 0x80
.fail:
    mov eax, 1
    mov ebx, 1
    int 0x80
.section .data
cases: .long 0,1,2,0x7fffffff,0x80000000,0xffffffff
expected: .long 0,1,1,1,1,1
