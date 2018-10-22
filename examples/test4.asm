LDSP 30
load_immediate r0, 1  # r0=1
load_immediate r1, 2  # r1=2
add r0, r0, r1        # r0=3
call 20               # r0=6
add r0, r0, r1        # r0=8
halt

20:
add r0, r0, r0
shl r0, r0  # r0=6
ret         # pc=(mem(29)=0), sr=(mem(30)=0)
halt

58:
:45
:87

# r0=8, r1=2, sp=30