load_immediate r0, 1
load_immediate r1, 2
load_immediate r2, 3
ldsp 30
push r0  # mem(30)=1, sp=29
push r0  # mem(29)=1, sp=28
push r1  # mem(28)=2, sp=27
ldsp 29
push r2  # mem(29)=3, sp=28
ldsp 28
pop r1   # r1=3
halt

# r0=1, r1=3, r2=3, mem(30)=1, mem(29)=3, mem(28)=2