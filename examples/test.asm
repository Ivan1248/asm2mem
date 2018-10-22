NOP
LOAD_IMMEDIATE R0, 8    # R0=8
LOAD_IMMEDIATE R1, -4   # R1=-4
ADD R0, R0, R1          # R0=4
LOAD_IMMEDIATE R2, 3    # R2=3
SUB R3, R1, R2          # R3=1 
SHL R0, R2              # R0=6
LOAD R0, 100            # R0=-5
LOAD_IMMEDIATE R3, 100  # R3=100
STORE RO, (R3)          # MEM(100)=6
HALT

# R0=-5, R1=-4, R2=3, R3=100, MEM(100)=6

100:
:-5