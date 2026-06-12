"""Verification helpers for the ALIGN-GF180 Wrapper.

The helpers mirror the summary/report style used by ``Gelochip_lib`` while
remaining self-contained inside the ``ALIGN-GF180 Wrapper`` folder.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


def parse_drc_report(report_content: str) -> dict[str, Any]:
    """Parse a Magic-style DRC report into a machine-readable summary."""

    errors: List[dict[str, str]] = []
    current_rule = ""
    for line in report_content.strip().splitlines():
        stripped_line = line.strip()
        if stripped_line == "----------------------------------------":
            continue
        if re.match(r"^[a-zA-Z]", stripped_line):
            current_rule = stripped_line
        elif re.match(r"^[0-9]", stripped_line):
            errors.append({"rule": current_rule, "details": stripped_line})

    is_pass = len(errors) == 0
    if not is_pass and re.search(r"count:\s*0\s*$", report_content, re.IGNORECASE):
        is_pass = True

    return {
        "is_pass": is_pass,
        "total_errors": len(errors),
        "error_details": errors,
    }


def parse_lvs_report(report_content: str) -> dict[str, Any]:
    """Parse a Netgen-style LVS report into a machine-readable summary."""

    summary: dict[str, Any] = {
        "is_pass": False,
        "conclusion": "LVS failed or report was inconclusive.",
        "total_mismatches": 0,
        "mismatch_details": {
            "nets": "Not found",
            "devices": "Not found",
            "unmatched_nets_parsed": [],
            "unmatched_instances_parsed": [],
        },
    }

    if "Netlists match" in report_content or "Circuits match uniquely" in report_content:
        summary["is_pass"] = True
        summary["conclusion"] = "LVS Pass: Netlists match."
    elif "Netlist mismatch" in report_content or "Netlists do not match" in report_content:
        summary["conclusion"] = "LVS Fail: Netlist mismatch."

    for line in report_content.splitlines():
        line = line.strip()
        net_mismatch_match = re.search(r"Net:\s*([^\|]+)\s*\|\s*\((no matching net)\)", line)
        if net_mismatch_match:
            name_left = net_mismatch_match.group(1).strip()
            summary["mismatch_details"]["unmatched_nets_parsed"].append(
                {
                    "type": "net",
                    "name": name_left,
                    "present_in": "layout",
                    "missing_in": "schematic",
                }
            )
            continue

        instance_mismatch_match = re.search(r"Instance:\s*([^\|]+)\s*\|\s*\((no matching instance)\)", line)
        if instance_mismatch_match:
            name_left = instance_mismatch_match.group(1).strip()
            summary["mismatch_details"]["unmatched_instances_parsed"].append(
                {
                    "type": "instance",
                    "name": name_left,
                    "present_in": "layout",
                    "missing_in": "schematic",
                }
            )
            continue

        net_mismatch_right_match = re.search(r"\s*\|\s*([^\|]+)\s*\((no matching net)\)", line)
        if net_mismatch_right_match:
            name_right = net_mismatch_right_match.group(1).strip()
            summary["mismatch_details"]["unmatched_nets_parsed"].append(
                {
                    "type": "net",
                    "name": name_right,
                    "present_in": "schematic",
                    "missing_in": "layout",
                }
            )
            continue

        instance_mismatch_right_match = re.search(r"\s*\|\s*([^\|]+)\s*\((no matching instance)\)", line)
        if instance_mismatch_right_match:
            name_right = instance_mismatch_right_match.group(1).strip()
            summary["mismatch_details"]["unmatched_instances_parsed"].append(
                {
                    "type": "instance",
                    "name": name_right,
                    "present_in": "schematic",
                    "missing_in": "layout",
                }
            )
            continue

        if "Number of devices:" in line:
            summary["mismatch_details"]["devices"] = line.split(":", 1)[1].strip()
        elif "Number of nets:" in line:
            summary["mismatch_details"]["nets"] = line.split(":", 1)[1].strip()

    summary["total_mismatches"] = (
        len(summary["mismatch_details"]["unmatched_nets_parsed"])
        + len(summary["mismatch_details"]["unmatched_instances_parsed"])
    )

    if summary["total_mismatches"] > 0:
        summary["is_pass"] = False
        if "LVS Pass" in summary["conclusion"]:
            summary["conclusion"] = "LVS Fail: Mismatches found."

    return summary


def netlist_translation_check(text: str) -> dict[str, Any]:
    """Check whether the translated netlist contains GF180 models and no SKY130 primitives."""

    sky130_hits = re.findall(r"\bsky130(?:_fd_pr__)?(?:nfet_01v8|pfet_01v8)\b", text, flags=re.IGNORECASE)
    gf180_hits = re.findall(r"\bgf180mcu_fd_pr__(?:nfet_10v5|pfet_10v5)\b", text, flags=re.IGNORECASE)
    has_pass = len(sky130_hits) == 0 and len(gf180_hits) > 0
    return {
        "is_pass": has_pass,
        "sky130_hits": sky130_hits,
        "gf180_hits": gf180_hits,
        "conclusion": "Translated netlist uses GF180 primitives." if has_pass else "Netlist translation incomplete.",
    }


@dataclass(frozen=True)
class VerificationPaths:
    """Artifact paths in the Gelochip-like layout."""

    root: Path
    drc_report: Path
    lvs_report: Path
    summary_json: Path
    summary_md: Path

    def as_dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in asdict(self).items()}
