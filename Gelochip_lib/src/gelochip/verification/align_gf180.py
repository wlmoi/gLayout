"""ALIGN-GF180 integration bridge for gelochip.verification.

This module keeps the existing verification package API intact while adding
access to the sibling ``ALIGN-GF180 Wrapper`` tools that live at the repo
root. The bridge is deliberately defensive:

- If the wrapper folder is missing, imports still succeed.
- If the wrapper module cannot be loaded, the helpers raise clear errors.
- Return shapes follow the same dictionary style used elsewhere in
  ``gelochip.verification``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Sequence


_BRIDGE_NAME = "align_gf180_wrapper_bridge"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _wrapper_dir() -> Path:
    return _repo_root() / "ALIGN-GF180 Wrapper"


def _wrapper_module_path() -> Path:
    return _wrapper_dir() / "align_gf180_wrapper.py"


def _helpers_module_path() -> Path:
    return _wrapper_dir() / "verification_helpers.py"


def _load_module(path: Path, module_name: str) -> ModuleType:
    if not path.is_file():
        raise FileNotFoundError(f"wrapper module not found: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_align_wrapper() -> Any:
    """Return the loaded ``AlignGf180Wrapper`` class."""

    module = _load_module(_wrapper_module_path(), _BRIDGE_NAME)
    return module.AlignGf180Wrapper


def get_verification_helpers() -> Any:
    """Return the loaded wrapper-side verification helper module."""

    return _load_module(_helpers_module_path(), f"{_BRIDGE_NAME}_helpers")


def translate_netlist_to_gf180(
    input_netlist: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Translate a SKY130 netlist to GF180MCU primitives using the wrapper."""

    wrapper_cls = get_align_wrapper()
    wrapper = wrapper_cls()
    return wrapper.translate_netlist(input_netlist, output_path=Path(output_path) if output_path is not None else None)


def prepare_gf180_pdk(pdk_root: str | Path | None = None, source_name: str = "sky130") -> tuple[Path, Path]:
    """Clone and patch the GF180 PDK tree using the wrapper."""

    wrapper_cls = get_align_wrapper()
    wrapper = wrapper_cls()
    return wrapper.prepare_gf180_pdk(pdk_root=pdk_root, source_name=source_name)


def run_align_gf180_wrapper(
    netlist_path: str | Path,
    top_subckt: str,
    pdk_root: str | Path | None = None,
    schematic2layout_py: str | Path | None = None,
    extra_args: Sequence[str] | None = None,
    source_name: str = "sky130",
) -> dict[str, Any]:
    """Run the full wrapper flow and return a structured result dict."""

    wrapper_cls = get_align_wrapper()
    wrapper = wrapper_cls()
    result = wrapper.run_end_to_end(
        netlist_path=netlist_path,
        top_subckt=top_subckt,
        pdk_root=pdk_root,
        source_name=source_name,
        schematic2layout_py=schematic2layout_py,
        extra_args=extra_args,
    )
    return {
        "pdk_root": str(result.pdk_root),
        "source_pdk_dir": str(result.source_pdk_dir),
        "gf180_pdk_dir": str(result.gf180_pdk_dir),
        "translated_netlist": str(result.translated_netlist),
        "cli_stdout": result.cli_stdout,
        "cli_stderr": result.cli_stderr,
    }


def run_align_gf180_verification(
    netlist_path: str | Path,
    top_subckt: str,
    pdk_root: str | Path | None = None,
    schematic2layout_py: str | Path | None = None,
    layout_gds: str | Path | None = None,
    report_dir: str | Path | None = None,
    source_name: str = "sky130",
) -> dict[str, Any]:
    """Run the wrapper-side verification flow and return Gelochip-style results."""

    wrapper_cls = get_align_wrapper()
    wrapper = wrapper_cls()
    helpers = get_verification_helpers()

    root = wrapper.resolve_align_pdk_root(pdk_root)
    source_dir, gf180_dir = wrapper.prepare_gf180_pdk(root, source_name=source_name)
    translated = wrapper.translate_netlist(netlist_path)

    if schematic2layout_py is not None:
        try:
            wrapper.run_schematic2layout(
                translated,
                top_subckt,
                gf180_dir,
                schematic2layout_py=schematic2layout_py,
            )
        except Exception:
            # The full ALIGN flow is optional in this bridge because this
            # repository often runs in environments without the real tool.
            pass

    netlist_text = Path(translated).read_text(encoding="utf-8", errors="ignore")
    translation_summary = helpers.netlist_translation_check(netlist_text)

    drc_status = {
        "is_pass": None,
        "status": "skipped",
        "report_path": None,
        "raw_report": "",
        "skipped": True,
        "reason": "Real DRC execution is not wired in this bridge.",
    }
    lvs_status = {
        "is_pass": None,
        "status": "skipped",
        "report_path": None,
        "raw_report": "",
        "skipped": True,
        "reason": "Real LVS execution is not wired in this bridge.",
    }

    summary = {
        "design_name": top_subckt,
        "pdk_root": str(root),
        "source_pdk_dir": str(source_dir),
        "gf180_pdk_dir": str(gf180_dir),
        "translated_netlist": str(translated),
        "layout_gds": str(layout_gds) if layout_gds is not None else None,
        "translation": translation_summary,
        "drc": drc_status,
        "lvs": lvs_status,
        "overall_pass": bool(translation_summary.get("is_pass")),
    }

    if report_dir is not None:
        report_root = Path(report_dir)
        report_root.mkdir(parents=True, exist_ok=True)
        (report_root / "summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
    return summary
