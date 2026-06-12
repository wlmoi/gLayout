v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N -280 -0 -280 20 {lab=VDD}
N -200 -10 -200 10 {lab=in1}
N -200 70 -200 90 {lab=0}
N -280 80 -280 100 {lab=0}
N -200 -10 -80 -10 {lab=in1}
N 120 20 200 20 {lab=out}
N 0 -140 0 -50 {lab=VDD}
N 0 100 0 160 {lab=0}
N -140 110 -140 130 {lab=0}
N -140 50 -80 50 {lab=in2}
C {gnd.sym} -280 100 0 0 {name=l1 lab=0}
C {vdd.sym} -280 0 0 0 {name=l2 lab=VDD}
C {vsource.sym} -280 50 0 0 {name=Vdd value=3.3 savecurrent=false}
C {gnd.sym} -200 90 0 0 {name=l3 lab=0}
C {vsource.sym} -200 40 0 0 {name=Vin1 value=0 savecurrent=false}
C {devices/code_shown.sym} -750 50 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {devices/code_shown.sym} -720 -800 0 0 {name=NGSPICE only_toplevel=true
value="
.control
save all

** Define input signal 1 (Fast clock)
let fsig = 2k
let Tper1 = 1/fsig
let Trise = 0.01*Tper1
let Ton1 = 0.5*Tper1 - 2*Trise

** Define input signal 2 (Slow clock - Twice the period)
let Tper2 = 2 * Tper1
let Ton2 = 0.5*Tper2 - 2*Trise

** Define transient params
let Tstop = 2*Tper1
let Tstep = 0.001*Tper1

** Set Sources
alter @Vin1[DC] = 0.0
alter @Vin2[DC] = 0.0
alter @Vin1[PULSE] = [ 0 3.3 0 $&Trise $&Trise $&Ton1 $&Tper1 0 ]
alter @Vin2[PULSE] = [ 0 3.3 0 $&Trise $&Trise $&Ton2 $&Tper2 0 ]

** Simulation
tran $&Tstep $&Tstop

** Plot output and inputs together in one window for easy comparison
setplot tran1
let vout = v(out)
plot vout

setplot tran2
let vin1 = v(in1)
let vin2 = v(in2)
plot vin1 vin2
write nand_gate_tb.raw
.endc
"}
C {noconn.sym} 200 20 2 0 {name=l4}
C {lab_wire.sym} -200 10 0 0 {name=p1 sig_type=std_logic lab=in1}
C {lab_wire.sym} 120 20 0 0 {name=p2 sig_type=std_logic lab=out}
C {gnd.sym} 0 160 0 0 {name=l5 lab=0}
C {vdd.sym} 0 -140 0 0 {name=l6 lab=VDD}
C {APIC/NAND_Gate/nand_gate.sym} -20 20 0 0 {name=x1}
C {gnd.sym} -140 130 0 0 {name=l7 lab=0}
C {vsource.sym} -140 80 0 0 {name=Vin2 value=0 savecurrent=false}
C {lab_wire.sym} -140 50 0 0 {name=p3 sig_type=std_logic lab=in2}
