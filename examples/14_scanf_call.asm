; BLOCK: RUN
extern scanf
global read_x

section .data
fmt db "%d", 0
x dd 0

section .text
read_x:
    ; IA-32 C caller enters with esp % 16 == 12 because CALL pushed 4 bytes.
    ; Reserve 4 bytes so two dword arguments leave esp % 16 == 0 before CALL.
    sub esp, 4
    push x
    push fmt
    call scanf
    add esp, 12

    mov eax, [x]
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
