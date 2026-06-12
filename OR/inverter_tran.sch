v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 230 -170 290 -170 {lab=Vin}
N 230 -170 230 -70 {lab=Vin}
N 230 -70 290 -70 {lab=Vin}
N 200 -120 230 -120 {lab=Vin}
N 330 -140 330 -100 {lab=Vout}
N 330 -120 370 -120 {lab=Vout}
N 330 -170 350 -170 {lab=VDD}
N 350 -200 350 -170 {lab=VDD}
N 330 -200 350 -200 {lab=VDD}
N 330 -70 350 -70 {lab=GND}
N 350 -70 350 -40 {lab=GND}
N 330 -40 350 -40 {lab=GND}
C {symbols/nfet_03v3_dss.sym} 310 -70 0 0 {name=M1
L=0.28u
W=0.22u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=nfet_03v3_dss
spiceprefix=X
}
C {symbols/pfet_03v3.sym} 310 -170 0 0 {name=M2
L=0.28u
W=0.22u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X
}
C {vdd.sym} 330 -200 0 0 {name=l1 lab=VDD}
C {gnd.sym} 330 -40 0 0 {name=l2 lab=GND}
C {vsource.sym} 70 -260 0 0 {name=Vdd value=3.3
 savecurrent=false}
C {vdd.sym} 70 -290 0 0 {name=l3 lab=VDD}
C {gnd.sym} 70 -230 0 0 {name=l4 lab=GND}
C {vsource.sym} 40 -90 0 0 {name=Vin value="pulse(0 3.3 1ns 1ns 1ns 4ns 10ns)"
 savecurrent=false}
C {gnd.sym} 40 -60 0 0 {name=l6 lab=GND}
C {code_shown.sym} 620 -120 2 1 {name=SIMULATIONS
only_toplevel=true
value="
.control
  save all
  tran 0.01n 1u
  write inverter_tran.raw
  plot vout
.endc
"}
C {lab_pin.sym} 200 -120 0 0 {name=p1 sig_type=std_logic lab=Vin
}
C {lab_pin.sym} 40 -120 1 0 {name=p2 sig_type=std_logic lab=Vin
}
C {lab_pin.sym} 370 -120 2 0 {name=p3 sig_type=std_logic lab=Vout

}
C {code.sym} 480 -250 0 0 {name=MODELS only_toplevel=true value="
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
"}
C {symbols/pfet_03v3.sym} 310 -170 0 0 {name=M3
L=0.28u
W=0.22u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X
}
