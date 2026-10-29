* +5V feed from the MES4-Carrier-EC (its bench PWR5, 27 Oct 2026): U1 URB2405S-6WR3 output -> C6 / C7 -> F2 1206L110 PTC
* -> FB1 BLM21PG121SN1D -> C8 / C9 at the M.2 socket -> node f5 (module fingers 20/22).
* The bench defines U1's output as a source Vu1 on node u1.
Ru1   u1 c524 0.1                             ; U1 load regulation
CC6   c524 0 15u Rser=5m                      ; 22 uF 25 V at 5 V
CC7   c524 0 100n Rser=20m
RF2   c524 cf2 0.12                           ; F2 cold
LFB1  cf2 f5 0.5u Rser=30m                    ; FB1, low-frequency model
RFB1  cf2 f5 120
CC8   f5 0 7u Rser=5m                         ; 10 uF 25 V at 5 V
CC9   f5 0 100n Rser=20m
