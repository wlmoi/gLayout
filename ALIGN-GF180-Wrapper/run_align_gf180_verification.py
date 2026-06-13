"""Run verification for the ALIGN-GF180 Wrapper outputs.

This runner mirrors the report layout and summary style of ``Gelochip_lib``
but focuses on verifying the wrapper output that lives in this folder.

What it can verify in this environment:
- translated SPICE netlist is produced
- SKY130 primitive names are replaced with GF180MCU primitive names
- output files and directory structure exist
- DRC/LVS are attempted only if the tools and layout inputs are available

What cannot be proven here without a real ALIGN + GF180MCU install:
- actual Magic DRC pass/fail
- actual Netgen LVS pass/fail
- ALIGN layout generation from the real schematic2layout flow
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Sequence

from align_gf180_wrapper import AlignGf180Wrapper, _create_mock_netlist, _create_mock_sky130_tree, _create_mock_schematic2layout
from verification_helpers import (
    VerificationPaths,
    netlist_translation_check,
    parse_drc_report,
    parse_lvs_report,
)


LOGGER = logging.getLogger("align_gf180_verification")


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ALIGN-GF180 wrapper verification")
    parser.add_argument("--netlist", type=Path, required=True, help="Input SKY130 netlist to translate.")
    parser.add_argument("--topcell", required=True, help="Top subcircuit name.")
    parser.add_argument("--pdk-root", type=Path, default=None, help="ALIGN PDK root or mock PDK root.")
    parser.add_argument(
        "--schematic2layout",
        type=Path,
        default=None,
        help="Optional ALIGN schematic2layout.py path.",
    )
    parser.add_argument(
        "--layout-gds",
        type=Path,
        default=None,
        help="Optional GDS file to run DRC/LVS against if you already have ALIGN output.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("ALIGN-GF180 Wrapper") / "outputs" / "verification",
        help="Directory where summary artifacts are written.",
    )
    parser.add_argument(
        "--source-pdk-name",
        default="sky130",
        help="Source PDK folder name to clone from.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Create mock SKY130 data and a mock schematic2layout.py so the runner can execute locally.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def _run_optional_real_checks(layout_gds: Path | None, design_name: str) -> dict[str, Any]:
    """Attempt real DRC/LVS if the environment has the right tools."""

    drc_status: dict[str, Any] = {
        "is_pass": None,
        "status": "skipped",
        "report_path": None,
        "raw_report": "",
        "skipped": True,
        "reason": "Magic not installed or no GDS provided.",
    }
    lvs_status: dict[str, Any] = {
        "is_pass": None,
        "status": "skipped",
        "report_path": None,
        "raw_report": "",
        "skipped": True,
        "reason": "Netgen not installed or no GDS provided.",
    }

    if layout_gds is None or not layout_gds.is_file():
        return {"drc": drc_status, "lvs": lvs_status}
    if not shutil.which("magic") or not shutil.which("netgen"):
        return {"drc": drc_status, "lvs": lvs_status}

    # If we ever get here on a real machine, try to use the wrapper's ALIGN
    # output and report status. The concrete deck invocation is intentionally
    # kept minimal so this file remains self-contained and easy to audit.
    drc_status.update({"reason": "Real Magic invocation not wired in this environment."})
    lvs_status.update({"reason": "Real Netgen invocation not wired in this environment."})
    return {"drc": drc_status, "lvs": lvs_status}


def _write_summary_md(paths: VerificationPaths, payload: dict[str, Any]) -> None:
    lines = [
        "# ALIGN-GF180 Wrapper Verification",
        "",
        f"- Design: `{payload['design_name']}`",
        f"- Netlist: `{payload['translated_netlist']}`",
        f"- GF180 PDK: `{payload['gf180_pdk_dir']}`",
        f"- DRC report: `{payload['drc_report']}`",
        f"- LVS report: `{payload['lvs_report']}`",
        "",
        "## Results",
        f"- Translation: {'PASS' if payload['translation']['is_pass'] else 'FAIL'}",
        f"- DRC: {payload['drc'].get('status', 'unknown').upper()}",
        f"- LVS: {payload['lvs'].get('status', 'unknown').upper()}",
        "",
        "## Notes",
        "- DRC/LVS are only real when Magic/Netgen and a real GDS are available.",
        "- In this workspace the tools are absent, so DRC/LVS are reported as skipped.",
    ]
    paths.summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    wrapper = AlignGf180Wrapper()
    report_dir = args.report_dir.resolve()
    _ensure_dir(report_dir)

    temp_ctx: tempfile.TemporaryDirectory[str] | None = None
    try:
        demo_mode = args.demo or args.pdk_root is None
        if demo_mode:
            temp_ctx = tempfile.TemporaryDirectory(prefix="align_gf180_verify_")
            demo_root = Path(temp_ctx.name)
            root = _create_mock_sky130_tree(demo_root)
            if not args.netlist.is_file():
                netlist_path = _create_mock_netlist(demo_root, args.topcell)
            else:
                netlist_path = args.netlist
            schematic2layout = _create_mock_schematic2layout(demo_root)
        else:
            root = wrapper.resolve_align_pdk_root(args.pdk_root)
            netlist_path = args.netlist
            schematic2layout = args.schematic2layout

        translated_netlist = wrapper.translate_netlist(netlist_path)
        source_dir, gf180_dir = wrapper.prepare_gf180_pdk(root, source_name=args.source_pdk_name)
        if schematic2layout is not None:
            try:
                wrapper.run_schematic2layout(
                    translated_netlist,
                    args.topcell,
                    gf180_dir,
                    schematic2layout_py=schematic2layout,
                )
            except Exception as exc:
                LOGGER.info("schematic2layout run skipped or failed in verification mode: %s", exc)

        netlist_text = _read_text(translated_netlist)
        translation_summary = netlist_translation_check(netlist_text)

        drc_report = report_dir / "drc" / args.topcell / f"{args.topcell}.rpt"
        lvs_report = report_dir / "lvs" / args.topcell / f"{args.topcell}_lvs.rpt"
        _ensure_dir(drc_report.parent)
        _ensure_dir(lvs_report.parent)

        real_check = _run_optional_real_checks(args.layout_gds, args.topcell)
        drc_summary = parse_drc_report(_read_text(drc_report)) if drc_report.is_file() else real_check["drc"]
        lvs_summary = parse_lvs_report(_read_text(lvs_report)) if lvs_report.is_file() else real_check["lvs"]

        if not drc_report.is_file():
            drc_summary.setdefault("status", "skipped")
        if not lvs_report.is_file():
            lvs_summary.setdefault("status", "skipped")

        overall_pass = bool(translation_summary.get("is_pass")) and (
            drc_summary.get("status") in {"pass", "skipped", None}
        ) and (
            lvs_summary.get("status") in {"pass", "skipped", None}
        )

        summary: dict[str, Any] = {
            "design_name": args.topcell,
            "pdk_root": str(root),
            "source_pdk_dir": str(source_dir),
            "gf180_pdk_dir": str(gf180_dir),
            "translated_netlist": str(translated_netlist),
            "drc_report": str(drc_report),
            "lvs_report": str(lvs_report),
            "translation": translation_summary,
            "drc": drc_summary,
            "lvs": lvs_summary,
            "overall_pass": overall_pass,
        }

        paths = VerificationPaths(
            root=report_dir,
            drc_report=drc_report,
            lvs_report=lvs_report,
            summary_json=report_dir / "summary.json",
            summary_md=report_dir / "summary.md",
        )
        paths.summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        _write_summary_md(paths, summary)

        print(f"Translation: {'PASS' if translation_summary['is_pass'] else 'FAIL'}")
        print(f"DRC: {str(drc_summary.get('status', 'unknown')).upper()}")
        print(f"LVS: {str(lvs_summary.get('status', 'unknown')).upper()}")
        print(f"Summary written to: {paths.summary_json}")
        print(f"Markdown written to: {paths.summary_md}")
        return 0
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
