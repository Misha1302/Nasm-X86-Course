; BLOCK: RUN
extern scanf
global read_x
section .data
fmt db "%d",0
x dd 0
section .text
read_x:
    ; Caller enters this function with ESP % 16 == 12 because CALL pushed
    ; the return address. Two dword arguments therefore need 4 bytes padding.
    sub esp, 4
    push x
    push fmt
    call scanf
    add esp, 12
    ret
section .note.GNU-stack noalloc noexec nowrite progbits
