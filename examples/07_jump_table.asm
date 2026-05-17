section .data
    fmtOut db "%d", 10, 0
    x dd 2

section .text
    extern printf
    global main

main:
    mov eax, [x]
    cmp eax, 3
    ja .default
    jmp [.table + 4*eax]

.table:
    dd .case0
    dd .case1
    dd .case2
    dd .case3

.case0:
    mov eax, 10
    jmp .print

.case1:
    mov eax, 20
    jmp .print

.case2:
    mov eax, 30
    jmp .print

.case3:
    mov eax, 40
    jmp .print

.default:
    xor eax, eax

.print:
    push eax
    push fmtOut
    call printf
    add esp, 8

    xor eax, eax
    ret
