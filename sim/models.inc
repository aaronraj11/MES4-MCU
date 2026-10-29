* Generic models for the MES4-MCU benches (datasheet-class, not vendor models), 29 Oct 2026
.model AO3400A VDMOS(Vto=1.05 Kp=25 Rd=12m Rs=6m Rg=1.5 Cgs=550p Cgdmax=250p Cgdmin=30p Cjo=150p Is=1e-12 Rb=8m)  ; Q3
.model D1N4148W D(Is=2.52n Rs=0.568 N=1.752 Cjo=4p M=0.4 Tt=20n BV=100 IBV=100u)                                ; D3 1N4148WS
.model MMBT3904 NPN(IS=1E-14 VAF=100 BF=300 IKF=0.4 XTB=1.5 BR=4 CJC=4E-12 CJE=8E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12 ITF=1 VTF=2 XTF=3)
* D2 SMF6.0A: VBR 6.67-7.37 V at 10 mA, VC 10.3 V at IPP 19.4 A (10/1000 us, 200 W)
.model SMF6V0A D(Is=1e-12 N=1 Rs=0.16 BV=7.0 IBV=10m Cjo=1.5n)
* D1 NUP2105L, one line: VBR 26.2-32 V at 1 mA, VC 37 V typ / 44 V max at 8 A (8/20 us), Rdyn ~1 ohm (TLP), CJ 26 pF typ
.model NUPZ D(Is=1e-12 N=1 Rs=0.5 BV=29 IBV=1m Cjo=52p M=0.33)                                                    ; two in anti-series = 26 pF
* LEDs, fitted to the Vf used in the Power sheet notes: red / yellow 2.0 V at 3 mA, green / white 2.8 V at 2 mA
.model LEDRY D(Is=8.6e-20 N=2 Rs=10 Cjo=20p BV=5 IBV=10u)
.model LEDGW D(Is=8.6e-27 N=2 Rs=10 Cjo=20p BV=5 IBV=10u)
.model DPROT D(Is=1e-14 N=1 Rs=10)                                                                                 ; GPIO clamp diode
.model DBODYLDO D(Is=1e-12 N=1.5 Rs=0.2)                                                                          ; U2 pass PMOS body diode

* U2 TLV76733: behavioural model fitted to TI SLVSE84D. UVLO 2.2 V rising / 130 mV hysteresis, 500 us soft-start,
* brickwall limit 1.3 A (1.1-1.6) with fold-back to 0.25 A (0.15-0.35) below 50 % VOUT, dropout 0.9 ohm (0.9 V typ at 1 A),
* no sinking, IQ 60 uA, body diode OUT -> IN. Loop: PI error amplifier (Kp 6 A/V, zero at 8 kHz) and a 0.15 us pass-device pole,
* tuned to TI Fig. 7-12 (250 -> 850 mA at 0.8 A/us, COUT 1 uF: about -120 mV / +100 mV, see bench MDL1).
* Supply ripple above 1 kHz reaches the reference at -60 dB (TI Fig. 9-4: 70 dB at 1 kHz, 46 dB at 100 kHz).
.subckt TLV76733 IN OUT GND
Ben en GND V=1/(1+exp(-(V(IN,GND)-2.135+0.13*(V(enf)-0.5))/10m))   ; UVLO comparator, 2.2 V on / 2.07 V off
Renf en enf 1k
Cenf enf GND 1n
Bss GND ss I=V(en)*6.6m*limit(20*(3.3-V(ss)),0,1)-(1-V(en))*10m*limit(V(ss),0,1)
Css ss GND 1u
Rss ss GND 1G
Chp IN hp 1n
Rhp hp GND 160k
Be e GND V=V(ss)+1m*V(hp)-V(OUT)
* current the pass device can give: fold-back limit or dropout (0.9 ohm), smooth minimum
Bia ia GND V=0.5*(min(1.3,0.25+1.05*max(V(OUT),0)/1.65)+max(V(IN,OUT),0)/0.9-sqrt((min(1.3,0.25+1.05*max(V(OUT),0)/1.65)-max(V(IN,OUT),0)/0.9)**2+1e-6))
Bint GND xi I=V(en)*3e5*V(e)*if(V(e)>0, limit(20*(V(ia)+0.02-V(xi)),0,1), limit(10*(V(xi)+0.1),0,1))-(1-V(en))*1e3*V(xi)
Cint xi GND 1
Rxi xi GND 1m
Bpc GND pc I=6*V(e)+V(xi)
Rpc pc GND 1
Cpc pc GND 0.15u
Bpass IN OUT I=V(en)*0.5*(max(V(pc),0)+max(V(ia),0)-sqrt((max(V(pc),0)-max(V(ia),0))**2+1e-6))
Dbody OUT IN DBODYLDO
Rfb OUT GND 330k
Bq IN GND I=60u*limit(V(IN),0,1)+1.5m*max(V(pc),0)*V(en)
Bpd OUT GND I=(1-V(en))*1.2m*limit(V(OUT),0,1)*limit(V(IN)-0.5,0,1)
.ends TLV76733

* U3 SN65HVD230 driver + receiver input (bus side only), TI SLOS346O. Dominant: CANH sourced from VCC - 0.1 V through Rh,
* CANL sunk to 0.75 V through Rl; open-circuit VOD 2.45 V. Rh + Rl = 13.5 ohm gives the typical VOD 2.0 V into 60 ohm,
* 38 ohm the minimum 1.5 V. Differential edges ~35-45 ns (Rs = 0, high-speed). Receiver input 35 kohm to 2.3 V, 20 pF per pin.
* VCC current: 10 mA quiescent + the bus current (dominant). Output current limited to 250 mA.
.subckt HVD230 D CANH CANL VCC GND params: Rd=13.5
Bdom GND dd I=if(V(D,GND)<1.4, 1, 0)
Rdd dd GND 1
Cdd dd GND 18n
Bh VCC CANH I=min(V(dd)*max(V(VCC,GND)-0.1-V(CANH,GND),0)/({Rd}/2), 0.25)
Bl CANL GND I=min(V(dd)*max(V(CANL,GND)-0.75,0)/({Rd}/2), 0.25)
Rih CANH b 35k
Ril CANL b 35k
Vb b GND 2.3
Cih CANH GND 20p
Cil CANL GND 20p
Rq VCC GND 330
.ends HVD230

* D1 NUP2105L, both lines (pins 1, 2 lines; pin 3 GND)
.subckt NUP2105L L1 L2 GND
Da1 m1 L1 NUPZ
Db1 m1 GND NUPZ
Da2 m2 L2 NUPZ
Db2 m2 GND NUPZ
.ends NUP2105L
