LOAD R1, 44
LOAD_IMMEDIATE R0, 3
NOP
add r0, r0, r1  # mogu se koristiti i mala slova

# "rucno" definirana instrukcija HALT
: 000011 00
: 0

44:  # podaci koji slijede pocinju od adrese 44
:53
:00100110
JZ R1, R2
:-12  # ovo je na adresi 48
