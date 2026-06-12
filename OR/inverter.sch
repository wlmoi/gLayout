v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 250 -160 250 -120 {lab=Y}
N 250 -140 290 -140 {lab=Y}
N 250 -190 270 -190 {lab=VP}
N 270 -220 270 -190 {lab=VP}
N 250 -220 270 -220 {lab=VP}
N 250 -90 270 -90 {lab=VN}
N 270 -90 270 -60 {lab=VN}
N 250 -60 270 -60 {lab=VN}
N 180 -190 210 -190 {lab=A}
N 180 -190 180 -90 {lab=A}
N 180 -90 210 -90 {lab=A}
N 150 -140 180 -140 {lab=A}
N 250 -240 250 -220 {lab=VP}
N 250 -60 250 -40 {lab=VN}
C {symbols/pfet_03v3.sym} 230 -190 0 0 {name=M3
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
C {ipin.sym} 150 -140 0 0 {name=p1 lab=A
}
C {iopin.sym} 250 -240 3 0 {name=p2 lab=VP
}
C {iopin.sym} 250 -40 1 0 {name=p3 lab=VN

}
C {opin.sym} 290 -140 0 0 {name=p4 lab=Y}
C {symbols/nfet_03v3.sym} 230 -90 0 0 {name=M2
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
