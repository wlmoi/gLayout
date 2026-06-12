v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 130 -260 160 -260 {lab=A}
N 200 -170 200 -150 {lab=#net1}
N 200 -150 200 -140 {lab=#net1}
N 90 -140 200 -140 {lab=#net1}
N 200 -140 300 -140 {lab=#net1}
N 90 -80 190 -80 {lab=GND}
N 190 -80 190 -50 {lab=GND}
N 190 -80 300 -80 {lab=GND}
N 130 -200 160 -200 {lab=B}
N 200 -160 380 -160 {lab=#net1}
N 440 -100 440 -50 {lab=GND}
N 400 -190 400 -130 {lab=#net1}
N 400 -190 400 -160 {lab=#net1}
N 380 -160 400 -160 {lab=#net1}
N 440 -290 440 -220 {lab=VDD}
N 440 -160 550 -160 {lab=Vout}
N 200 -260 230 -260 {lab=VDD}
N 230 -290 230 -260 {lab=VDD}
N 200 -290 230 -290 {lab=VDD}
N 200 -200 230 -200 {lab=VDD}
N 230 -230 230 -200 {lab=VDD}
N 90 -110 110 -110 {lab=GND}
N 110 -110 110 -80 {lab=GND}
N 280 -110 300 -110 {lab=GND}
N 280 -110 280 -80 {lab=GND}
N 440 -190 460 -190 {lab=VDD}
N 460 -220 460 -190 {lab=VDD}
N 440 -220 460 -220 {lab=VDD}
N 440 -130 460 -130 {lab=GND}
N 460 -130 460 -100 {lab=GND}
N 440 -100 460 -100 {lab=GND}
N 230 -260 230 -230 {lab=VDD}
C {symbols/pfet_03v3.sym} 180 -260 0 0 {name=M2
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
C {vdd.sym} 200 -290 0 0 {name=l1 lab=VDD}
C {gnd.sym} 190 -50 0 0 {name=l2 lab=GND}
C {symbols/nfet_03v3.sym} 70 -110 0 0 {name=M4
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
model=nfet_03v3
spiceprefix=X
}
C {lab_pin.sym} 130 -260 0 0 {name=p1 sig_type=std_logic lab=A
}
C {lab_pin.sym} 130 -200 0 0 {name=p2 sig_type=std_logic lab=B

}
C {lab_pin.sym} 50 -110 0 0 {name=p3 sig_type=std_logic lab=A
}
C {lab_pin.sym} 340 -110 2 0 {name=p4 sig_type=std_logic lab=B

}
C {lab_pin.sym} 550 -160 2 0 {name=p5 sig_type=std_logic lab=Vout

}
C {code.sym} 10 -500 0 0 {name=MODELS only_toplevel=true value="
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
"}
C {code_shown.sym} 150 -410 2 1 {name=SIMULATIONS
only_toplevel=true
value="
.control
  save all
  * Run a 40 nanosecond transient simulation
  tran 100p 40n
  
  * Force ngspice to save the raw file exactly where you want it:
  write /foss/designs/orgate_truth_table.raw
  
  * Plot A, B, and Output with voltage offsets for stacking
  plot v(a)+8 v(b)+4 v(out)
.endc
"}
C {vsource.sym} 620 -300 0 0 {name=Vdd value=3.3
 savecurrent=false}
C {vdd.sym} 620 -330 0 0 {name=l3 lab=VDD}
C {gnd.sym} 620 -270 0 0 {name=l4 lab=GND}
C {vsource.sym} 650 -180 0 0 {name=Vin value="PULSE(0 3.3 0 0.1n 0.1n 20n 40n)"
 savecurrent=false}
C {gnd.sym} 650 -150 0 0 {name=l6 lab=GND}
C {vsource.sym} 720 -310 0 0 {name=Vin1 value="PULSE(0 3.3 0 0.1n 0.1n 10n 20n)"
 savecurrent=false}
C {gnd.sym} 720 -280 0 0 {name=l5 lab=GND}
C {lab_pin.sym} 720 -340 1 0 {name=p7 sig_type=std_logic lab=A
}
C {symbols/pfet_03v3.sym} 180 -200 0 0 {name=M1
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
C {symbols/nfet_03v3.sym} 320 -110 0 1 {name=M3
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
model=nfet_03v3
spiceprefix=X
}
C {symbols/pfet_03v3.sym} 420 -190 0 0 {name=M5
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
C {symbols/nfet_03v3.sym} 420 -130 0 0 {name=M6
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
model=nfet_03v3
spiceprefix=X
}
C {gnd.sym} 440 -50 0 0 {name=l7 lab=GND}
C {vdd.sym} 440 -290 0 0 {name=l8 lab=VDD}
C {lab_pin.sym} 650 -210 1 0 {name=p6 sig_type=std_logic lab=B
}
