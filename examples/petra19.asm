load_immediate r0, 1   # r0=1
load_immediate r1, -2  # r1=-2
eq r2, r0, r1          # r2=0
eq r3, r1, r0          # r0=0
eq r1, r1, r1          # r1=1
halt
