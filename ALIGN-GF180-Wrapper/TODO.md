# TODO - ALIGN-GF180 real DRC/LVS invocation

- [ ] (1) Update `run_align_gf180_verification.py`: add `sys` + `sys.path.append(...)` for Gelochip scripts.
- [ ] (2) Update `_run_optional_real_checks(...)` to remove skip-by-design and actually attempt Gelochip `pdk.drc_magic` and `pdk.lvs_netgen` when tools exist.
- [ ] (3) Update `main()` to force GDS path to `/foss/designs/FullAdder.gds` (or make it configurable) so real checks are attempted.
- [ ] (4) Run `python3 run_align_gf180_verification.py ...` in container to confirm `DRC:` and `LVS:` results are not `SKIPPED`.
- [ ] (5) If import fails, capture error and adjust sys.path/import path accordingly.

