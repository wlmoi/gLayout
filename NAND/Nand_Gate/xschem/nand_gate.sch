v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N 0 190 0 210 {lab=Vss}
N -200 -70 -180 -70 {lab=in1}
N 0 -0 70 -0 {lab=out}
N 0 100 -0 130 {lab=#net1}
N 0 0 -0 40 {lab=out}
N -0 -30 0 -0 {lab=out}
N 0 -30 80 -30 {lab=out}
N 80 -40 80 -30 {lab=out}
N -80 -30 0 -30 {lab=out}
N -80 -40 -80 -30 {lab=out}
N -80 -110 -80 -100 {lab=Vdd}
N -80 -110 0 -110 {lab=Vdd}
N -0 -110 80 -110 {lab=Vdd}
N 80 -110 80 -100 {lab=Vdd}
N -0 -120 -0 -110 {lab=Vdd}
N -180 -70 -120 -70 {lab=in1}
N -150 70 -40 70 {lab=in1}
N -150 -70 -150 70 {lab=in1}
N -180 160 -40 160 {lab=in2}
N -180 0 -180 160 {lab=in2}
N -180 0 -20 -0 {lab=in2}
N -20 -70 -20 -0 {lab=in2}
N -20 -70 40 -70 {lab=in2}
N -200 0 -180 -0 {lab=in2}
N -80 -70 -60 -70 {lab=Vdd}
N -60 -110 -60 -70 {lab=Vdd}
N 80 -70 110 -70 {lab=Vdd}
N 110 -110 110 -70 {lab=Vdd}
N 80 -110 110 -110 {lab=Vdd}
N 0 160 30 160 {lab=Vss}
N 30 160 30 200 {lab=Vss}
N -0 200 30 200 {lab=Vss}
N 30 70 30 160 {lab=Vss}
N -0 70 30 70 {lab=Vss}
C {ipin.sym} -200 -70 0 0 {name=p1 lab=in1}
C {opin.sym} 70 0 0 0 {name=p2 lab=out}
C {symbols/pfet_03v3.sym} 60 -70 0 0 {name=M3
L=0.28u
W=2.00u
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
C {symbols/nfet_03v3.sym} -20 70 0 0 {name=M1
L=1.00u
W=0.42u
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
C {ipin.sym} 0 -120 1 0 {name=p3 lab=Vdd}
C {ipin.sym} 0 210 3 0 {name=p4 lab=Vss}
C {symbols/pfet_03v3.sym} -100 -70 0 0 {name=M2
L=0.28u
W=2.00u
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
C {symbols/nfet_03v3.sym} -20 160 0 0 {name=M4
L=1.00u
W=0.42u
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
C {ipin.sym} -200 0 0 0 {name=p5 lab=in2}
