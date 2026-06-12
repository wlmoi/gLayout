v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {vdd.sym} 300 -120 0 0 {name=l1 lab=VDD}
C {gnd.sym} 300 -60 0 0 {name=l2 lab=GND}
C {vsource.sym} 80 -150 0 0 {name=Vdd value=3.3
 savecurrent=false}
C {vdd.sym} 80 -180 0 0 {name=l3 lab=VDD}
C {gnd.sym} 80 -120 0 0 {name=l4 lab=GND}
C {vsource.sym} 20 -70 0 0 {name=Vin value="pulse(0 3.3 1ns 1ns 1ns 4ns 10ns)"
 savecurrent=false}
C {gnd.sym} 20 -40 0 0 {name=l6 lab=GND}
C {lab_pin.sym} 20 -100 1 0 {name=p2 sig_type=std_logic lab=Vin
}
C {lab_pin.sym} 270 -90 0 0 {name=p1 sig_type=std_logic lab=Vin}
C {/foss/designs/inverter.sym} 240 -90 0 0 {name=X2}
C {lab_pin.sym} 340 -90 2 0 {name=p3 sig_type=std_logic lab=Vout}
C {code_shown.sym} 570 -50 2 1 {name=SIMULATIONS
only_toplevel=true
value="
.control
  save all
  tran 0.01n 1u
  write inverter_sym.raw
  plot vout
.endc
"}
C {code.sym} 430 -180 0 0 {name=MODELS only_toplevel=true value="
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
"}
