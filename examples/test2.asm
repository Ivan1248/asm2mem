load_immediate r0, 0
load_immediate r1, 10
load_immediate r2, 20
jmp 20 
halt

20:
add r3, r1, r2  # r3=30
jz r1, r1       # nop
move r2, r1     # r2=10
jmp 10

10:
jz r0, r3        # jmp 30
halt

30:
move r3, r1     # r3=10
halt

# r0=0, r1=10, r2=10, r3=10