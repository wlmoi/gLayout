# ALIGN-GF180 Wrapper Verification

This folder contains a Python wrapper that prepares an ALIGN PDK tree for GF180MCU by:

1. locating the ALIGN internal PDK root,
2. cloning `sky130` to `gf180mcu`,
3. patching ALIGN-style JSON rule files,
4. translating SKY130 primitive device names in SPICE netlists, and
5. invoking ALIGN's `schematic2layout.py` through `subprocess.run(...)`.

## Verified On This Machine

I ran the local verification flow against the OTA example netlist in this folder.

- Input: [telescopic_ota_sky130_example.sp](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\telescopic_ota_sky130_example.sp)
- Output: [telescopic_ota_sky130_example_gf180.sp](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\telescopic_ota_sky130_example_gf180.sp)
- Summary JSON: [outputs/verification/summary.json](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\outputs\verification\summary.json)
- Summary MD: [outputs/verification/summary.md](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\outputs\verification\summary.md)

Observed result:

- Translation: `PASS`
- DRC: `SKIPPED`
- LVS: `SKIPPED`
- Overall: `PASS` for the wrapper workflow itself

Why DRC/LVS were skipped:

- `magic` is not installed on this machine.
- `netgen` is not installed on this machine.
- `klayout` is not installed on this machine.
- There is no real ALIGN-generated GDS artifact available in this workspace to run physical checks against.

## Report Format

The wrapper-side verification runner mirrors the structure used in `Gelochip_lib`:

- `outputs/verification/drc/<design>/<design>.rpt`
- `outputs/verification/lvs/<design>/<design>_lvs.rpt`
- `outputs/verification/summary.json`
- `outputs/verification/summary.md`

The generated `summary.json` for the OTA example includes:

- `design_name`: `telescopic_ota`
- `translation.is_pass`: `true`
- `drc.status`: `skipped`
- `lvs.status`: `skipped`
- `overall_pass`: `true`

## OTA Translation Example

Input excerpt:

```spice
.subckt telescopic_ota vbiasn vbiasp1 vbiasp2 vinn vinp voutn voutp vdd 0
m1 id id 0 0 nfet_03v3 w=1.05e-6 l=150e-9 nf=2
m8 voutp vbiasp1 net012 vdd pfet_03v3 w=1.05e-6 l=150e-9 nf=2
.ends telescopic_ota
```

Translated excerpt:

```spice
.subckt telescopic_ota vbiasn vbiasp1 vbiasp2 vinn vinp voutn voutp vdd 0
m1 id id 0 0 gf180mcu_fd_pr__nfet_10v5 w=1.05e-6 l=150e-9 nf=2
m8 voutp vbiasp1 net012 vdd gf180mcu_fd_pr__pfet_10v5 w=1.05e-6 l=150e-9 nf=2
.ends telescopic_ota
```

The wrapper writes this to a new file with the `_gf180.sp` suffix.

## DRC Check

### What the wrapper-side verifier does

- Prepares a GF180MCU PDK tree by cloning `sky130` into `gf180mcu`.
- Rewrites the rule JSON files that ALIGN consumes.
- Looks for a real GDS artifact and the `magic` tool.
- If both are missing, it marks DRC as `skipped` instead of pretending it passed.

### What still requires a real install

- The actual DRC run is performed by Magic against a real GDS layout.

## LVS Check

### What the wrapper-side verifier does

- Translates SKY130 primitive model names to GF180MCU primitive model names.
- Keeps the subcircuit name intact.
- Looks for a real GDS artifact and the `netgen` tool.
- If either is missing, it marks LVS as `skipped` instead of pretending it passed.

### What still requires a real install

- The actual LVS result depends on a real ALIGN-generated layout, Magic, and Netgen.

## Files Added In This Folder

- [align_gf180_wrapper.py](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\align_gf180_wrapper.py)
- [verification_helpers.py](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\verification_helpers.py)
- [run_align_gf180_verification.py](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\run_align_gf180_verification.py)
- [VERIFICATION.md](D:\LinkedinProjects\gLayout\ALIGN-GF180%20Wrapper\VERIFICATION.md)

## How To Run

Demo verification with the OTA example:

```powershell
& 'C:\Users\William Anthony\Miniconda3\python.exe' 'ALIGN-GF180 Wrapper\run_align_gf180_verification.py' --demo --netlist 'ALIGN-GF180 Wrapper\telescopic_ota_sky130_example.sp' --topcell telescopic_ota
```

Real mode:

```powershell
& 'C:\Users\William Anthony\Miniconda3\python.exe' 'ALIGN-GF180 Wrapper\run_align_gf180_verification.py' `
  --pdk-root "D:\path\to\align\pdk" `
  --netlist "D:\path\to\telescopic_ota.sp" `
  --topcell telescopic_ota `
  --layout-gds "D:\path\to\telescopic_ota.gds" `
  --schematic2layout "D:\path\to\schematic2layout.py"
```

## Notes

- The wrapper is intentionally conservative about file discovery and will raise a clear exception if the expected PDK or CLI entry point cannot be found.
- The JSON rewrite logic is recursive, so it can handle both the named ALIGN config files and any additional JSON files that still contain SKY130 tokens.
