DEFINE EQ AS EQUAL

main:
    LDI R2 2
    LDI R3 13
    LDI R4 64
    LDI R6 1
    STR R4 R0
    LDI R5 16
    STR R5 R6
    LDI R1 8
    CAL loop
    LDI R1 5
    CAL loop
    LDI R1 12
    CAL loop
    LDI R1 12
    CAL loop
    LDI R1 15
    CAL loop
    LDI R1 0
    CAL loop
    LDI R1 23
    CAL loop
    LDI R1 15
    CAL loop
    LDI R1 18
    CAL loop
    LDI R1 12
    CAL loop
    LDI R1 4
    CAL loop
    LDI R2 2

show:
    OUT 12 R2
    OUT 13 R0
    ADI R2 1
    CMP R2 R3
    BRH EQ fin
    JMP show




fin:
    OUT 13 R6
    HLT

loop:
    STR R1 R2
    INC R2
    RET
