; BLOCK: COMPILE
extern scanf
global read_x
section .data
fmt db "%d",0
x dd 0
section .text
read_x:
    sub esp, 8
    push x
    push fmt
    call scanf
    add esp, 16
    ret
section .note.GNU-stack noalloc noexec nowrite progbits
