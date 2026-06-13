* Example OTA netlist for ALIGN-GF180 wrapper verification
.subckt telescopic_ota vbiasn vbiasp1 vbiasp2 vinn vinp voutn voutp vdd 0
m1 id id 0 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=2
m2 net10 id 0 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=2
m5 voutn vbiasn net8 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=2
m6 voutp vbiasn net014 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=2
m8 voutp vbiasp1 net012 vdd gf180mcu_fd_pr__pfet_10v5 w=1.05e-6 l=150e-9 nf=2
m7 voutn vbiasp1 net06 vdd gf180mcu_fd_pr__pfet_10v5 w=1.05e-6 l=150e-9 nf=2
m10 net012 vbiasp2 vdd vdd gf180mcu_fd_pr__pfet_10v5 w=1.05e-6 l=150e-9 nf=2
m9 net06 vbiasp2 vdd vdd gf180mcu_fd_pr__pfet_10v5 w=1.05e-6 l=150e-9 nf=2
m4 net014 vinn net10 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=4
m3 net8 vinp net10 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=4
.ends telescopic_ota
** End of subcircuit definition.
