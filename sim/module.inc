* MES4-MCU power network (Power sheet 2, MCU sheet 3), values from the schematic Rev A-d6, 29 Oct 2026.
* Node fin = M.2 fingers 20/22, v5 = +5V, v3 = +3V3, pb2 = VSENSE_5V. Needs models.inc and the parameters
* pb4 / pb5 (LED GPIO levels, 0 or 3.3) and Icar (carrier load on pin 4, A).
* Ceramic 10 uF 25 V 0805 caps are modelled at their DC-bias value: about 5 uF at 5 V, 6.9 uF at 3.3 V (Power sheet notes).
Lfin fin v5 3n Rser=5m                         ; fingers 20 + 22 and the socket contacts in parallel
C1  v5 0 5u Rser=5m
C10 v5 0 100n Rser=20m
D2  0 v5 SMF6V0A
Vu2 v5 u2in 0                                 ; ammeter: U2 input current
XU2 u2in v3 0 TLV76733
C2  v3 0 6.9u Rser=5m                         ; at U2
C3  v3 0 100n Rser=20m
C5  v3 0 6.9u Rser=5m                         ; at U1 pin 4
C4  v3 0 100n Rser=20m
C7  v3 0 100n Rser=20m                        ; X1
C8  v3 0 100n Rser=20m                        ; U3
* 3V3 loads that only need the rail to be up (U3 is added per bench where its bus current matters)
B_MCU v3 0 I=20m*limit((V(v3)-1.6)/0.4,0,1)  ; STM32G0B1 at 64 MHz, all peripherals (Power notes)
B_X1  v3 0 I=10m*limit((V(v3)-1.4)/0.2,0,1)  ; SX2M Icc max
B_CAR v3 0 I={Icar}*limit(V(v3)/3.3,0,1)     ; carrier loads on M.2 pin 4
* LED1 red (+5V), LED2 green (+3V3 present, Q4), LED3 white (CAN, PB4, Q1), LED4 yellow (USR, PB5, Q2)
R1  v5 l1a 1k
DL1 l1a 0 LEDRY
R2  v5 l2a 1k
DL2 l2a l2k LEDGW
Q4  l2k l2b 0 MMBT3904
R13 v3 l2b 10k
R3  v5 l3a 1k
DL3 l3a l3k LEDGW
Q1  l3k l3b 0 MMBT3904
R5  pb4 l3b 10k
Vpb4 pb4 0 {pb4}
R4  v5 l4a 1k
DL4 l4a l4k LEDRY
Q2  l4k l4b 0 MMBT3904
R6  pb5 l4b 10k
Vpb5 pb5 0 {pb5}
* VSENSE_5V: R8 20k / R9 10k / C9 100 nF -> PB2 (FT_ea pin, no diode to VDD)
R8  v5 pb2 20k
R9  pb2 0 10k
C9  pb2 0 100n Rser=20m
