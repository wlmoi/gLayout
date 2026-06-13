"""ALIGN-GF180 Wrapper.

This module clones an ALIGN-internal SKY130 PDK tree into a GF180MCU PDK
tree, rewrites key JSON rule files, translates legacy SKY130 primitive
device names in SPICE netlists, and wraps ALIGN's ``schematic2layout.py``
CLI in a subprocess helper with robust error reporting.

The module is intentionally self-contained so it can be dropped into the
``ALIGN-GF180 Wrapper`` folder and run immediately. The ``__main__`` block
creates a mock SKY130 PDK tree and a mock ALIGN CLI when you want to test
the complete flow without a real ALIGN install.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


LOGGER = logging.getLogger("align_gf180_wrapper")


class AlignGf180Error(RuntimeError):
    """Base exception for the wrapper."""


class PDKNotFoundError(AlignGf180Error):
    """Raised when the ALIGN-internal PDK root cannot be located."""


class NetlistTranslationError(AlignGf180Error):
    """Raised when a netlist cannot be translated."""


class AlignCommandError(AlignGf180Error):
    """Raised when ALIGN's ``schematic2layout.py`` fails."""

    def __init__(
        self,
        message: str,
        *,
        returncode: int,
        stdout: str,
        stderr: str,
        command: Sequence[str],
    ) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = list(command)


@dataclass(frozen=True)
class GF180Profile:
    """GF180MCU-specific replacements used while patching ALIGN PDK files."""

    pdk_folder_name: str = "gf180mcu"
    source_pdk_names: Tuple[str, ...] = ("sky130", "sky130A")
    sky130_to_gf180_models: Mapping[str, str] = field(
        default_factory=lambda: {
            "sky130_fd_pr__nfet_01v8": "gf180mcu_fd_pr__nfet_10v5",
            "sky130_fd_pr__pfet_01v8": "gf180mcu_fd_pr__pfet_10v5",
            "nfet_03v3": "gf180mcu_fd_pr__nfet_10v5",
            "pfet_03v3": "gf180mcu_fd_pr__pfet_10v5",
        }
    )
    abstract_layer_ids: Mapping[str, Tuple[int, int]] = field(
        default_factory=lambda: {
            "metal5": (81, 0),
            "via4": (41, 0),
            "metal4": (46, 0),
            "via3": (40, 0),
            "metal3": (42, 0),
            "via2": (38, 0),
            "metal2": (36, 0),
            "via1": (35, 0),
            "metal1": (34, 0),
            "contact": (33, 0),
            "poly2": (30, 0),
            "comp": (22, 0),
            "nplus": (32, 0),
            "pplus": (31, 0),
            "nwell": (21, 0),
            "lvpwell": (204, 0),
            "dnwell": (12, 0),
            "CAP_MK": (117, 5),
            "drc_bjt": (127, 5),
            "lvs_bjt": (118, 5),
            "metal5_label": (81, 10),
            "metal4_label": (46, 10),
            "metal3_label": (42, 10),
            "metal2_label": (36, 10),
            "metal1_label": (34, 10),
            "poly2_label": (30, 10),
            "comp_label": (22, 10),
        }
    )
    abstract_layer_name_aliases: Mapping[str, str] = field(
        default_factory=lambda: {
            "met5": "metal5",
            "via4": "via4",
            "met4": "metal4",
            "via3": "via3",
            "met3": "metal3",
            "via2": "via2",
            "met2": "metal2",
            "via1": "via1",
            "met1": "metal1",
            "mcon": "contact",
            "poly": "poly2",
            "active_diff": "comp",
            "active_tap": "comp",
            "n+s/d": "nplus",
            "p+s/d": "pplus",
            "nwell": "nwell",
            "pwell": "lvpwell",
            "dnwell": "dnwell",
            "capmet": "CAP_MK",
            "drc_bjt": "drc_bjt",
            "lvs_bjt": "lvs_bjt",
            "met5_pin": "metal5_label",
            "met4_pin": "metal4_label",
            "met3_pin": "metal3_label",
            "met2_pin": "metal2_label",
            "met1_pin": "metal1_label",
            "poly_pin": "poly2_label",
            "active_diff_pin": "comp_label",
            "met5_label": "metal5_label",
            "met4_label": "metal4_label",
            "met3_label": "metal3_label",
            "met2_label": "metal2_label",
            "met1_label": "metal1_label",
            "poly_label": "poly2_label",
            "active_diff_label": "comp_label",
        }
    )
    numeric_field_defaults: Mapping[str, float] = field(
        default_factory=lambda: {
            "manufacturing_grid": 0.005,
            "grid": 0.005,
            "grid_pitch": 0.005,
            "pitch": 0.005,
            "resolution": 0.001,
            "precision": 5e-9,
            "dbu": 0.001,
        }
    )
    rule_file_names: Tuple[str, ...] = ("layers.json", "min_width_rules.json")


@dataclass(frozen=True)
class WrapperRunResult:
    """A structured return value for an end-to-end wrapper run."""

    pdk_root: Path
    source_pdk_dir: Path
    gf180_pdk_dir: Path
    translated_netlist: Path
    cli_stdout: str = ""
    cli_stderr: str = ""


class AlignGf180Wrapper:
    """Object-oriented wrapper that manages the SKY130 to GF180MCU migration."""

    def __init__(
        self,
        profile: GF180Profile | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.profile = profile or GF180Profile()
        self.logger = logger or LOGGER

    # ---------------------------------------------------------------------
    # PDK discovery and cloning
    # ---------------------------------------------------------------------
    def resolve_align_pdk_root(self, explicit: Path | str | None = None) -> Path:
        """Locate the ALIGN internal PDK root directory.

        Search order:
        1. Explicit path supplied by the caller.
        2. Environment variables: ``ALIGN_PDK_ROOT``, ``PDK_ROOT``,
           ``ALIGN_HOME``, ``ALIGN_ROOT``, ``ALIGN_PATH``.
        3. Common local installation guesses, including the current workspace
           and ``CONDA_PREFIX/share/pdk``.
        """

        if explicit is not None:
            root = Path(explicit).expanduser().resolve()
            resolved = self._resolve_root_from_candidate(root)
            if resolved is not None:
                return resolved
            raise PDKNotFoundError(f"explicit PDK root does not exist: {root}")

        env_candidates = [
            os.environ.get("ALIGN_PDK_ROOT"),
            os.environ.get("PDK_ROOT"),
            os.environ.get("ALIGN_HOME"),
            os.environ.get("ALIGN_ROOT"),
            os.environ.get("ALIGN_PATH"),
        ]
        for candidate in env_candidates:
            if not candidate:
                continue
            root = Path(candidate).expanduser()
            if root.is_dir():
                resolved = self._resolve_root_from_candidate(root)
                if resolved is not None:
                    return resolved

        conda_prefix = os.environ.get("CONDA_PREFIX")
        if conda_prefix:
            pdk_guess = Path(conda_prefix) / "share" / "pdk"
            resolved = self._resolve_root_from_candidate(pdk_guess)
            if resolved is not None:
                return resolved

        for base in self._common_search_bases():
            resolved = self._resolve_root_from_candidate(base)
            if resolved is not None:
                return resolved

        raise PDKNotFoundError(
            "Unable to locate the ALIGN PDK root. "
            "Pass --pdk-root or set ALIGN_PDK_ROOT/PDK_ROOT."
        )

    def _common_search_bases(self) -> Iterable[Path]:
        cwd = Path.cwd()
        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parent
        bases = [
            cwd,
            cwd.parent,
            script_dir,
            repo_root,
        ]
        seen: set[Path] = set()
        for base in bases:
            try:
                resolved = base.resolve()
            except OSError:
                continue
            if resolved not in seen and resolved.exists():
                seen.add(resolved)
                yield resolved

    def _resolve_root_from_candidate(self, root: Path) -> Path | None:
        """Return the actual PDK root if the candidate contains SKY130."""

        if self._looks_like_pdk_root(root):
            return root.resolve()

        if root.is_dir() and root.name.lower() in {name.lower() for name in self.profile.source_pdk_names}:
            parent = root.parent
            if self._looks_like_pdk_root(parent):
                return parent.resolve()

        for direct in self._direct_pdk_containers(root):
            if self._looks_like_pdk_root(direct):
                return direct.resolve()
        return None

    def _direct_pdk_containers(self, root: Path) -> Iterable[Path]:
        candidates = [
            root / "share" / "pdk",
            root / "pdk",
            root / "PDK",
            root / "pdks",
        ]
        for candidate in candidates:
            if candidate.is_dir():
                yield candidate

    def _looks_like_pdk_root(self, root: Path) -> bool:
        for name in self.profile.source_pdk_names:
            if (root / name).is_dir():
                return True
        return False

    def find_source_pdk_dir(self, pdk_root: Path, source_name: str = "sky130") -> Path:
        """Find the SKY130 source PDK directory inside the ALIGN PDK root."""

        root = pdk_root.resolve()
        candidates = [
            root / source_name,
            root / f"{source_name}A",
        ]
        for candidate in candidates:
            if candidate.is_dir():
                return candidate

        for child in root.iterdir():
            if child.is_dir() and child.name.lower() in {source_name.lower(), f"{source_name.lower()}a"}:
                return child.resolve()

        raise FileNotFoundError(
            f"Could not find a SKY130 PDK directory under {root}. "
            f"Expected one of: {source_name}, {source_name}A."
        )

    def clone_sky130_to_gf180(
        self,
        pdk_root: Path,
        source_name: str = "sky130",
        target_name: str | None = None,
    ) -> Path:
        """Clone the SKY130 PDK tree into a GF180MCU sibling tree."""

        target_name = target_name or self.profile.pdk_folder_name
        source_dir = self.find_source_pdk_dir(pdk_root, source_name=source_name)
        target_dir = source_dir.parent / target_name

        if target_dir.exists():
            self.logger.info("GF180MCU PDK already exists: %s", target_dir)
            return target_dir.resolve()

        self.logger.info("Cloning %s -> %s", source_dir, target_dir)
        shutil.copytree(source_dir, target_dir)
        return target_dir.resolve()

    # ---------------------------------------------------------------------
    # JSON patching
    # ---------------------------------------------------------------------
    def patch_gf180_pdk_jsons(self, gf180_dir: Path) -> List[Path]:
        """Rewrite key ALIGN JSON files in the cloned GF180MCU PDK tree."""

        gf180_dir = gf180_dir.resolve()
        modified: List[Path] = []
        seen_targets: set[Path] = set()

        for file_name in self.profile.rule_file_names:
            for path in gf180_dir.rglob(file_name):
                if path.is_file():
                    if path not in seen_targets:
                        if self._patch_single_json(path):
                            modified.append(path)
                        seen_targets.add(path)

        # If the exact filenames are not present, patch any JSON file that still
        # contains SKY130 tokens so the tree is usable in a mock ALIGN layout.
        for path in gf180_dir.rglob("*.json"):
            if path in seen_targets or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "sky130" in text.lower() or "sky130a" in text.lower():
                if self._patch_single_json(path):
                    modified.append(path)
        return modified

    def _patch_single_json(self, path: Path) -> bool:
        """Load, patch, and write one JSON file."""

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AlignGf180Error(f"Invalid JSON in {path}: {exc}") from exc

        patched, changed = self._patch_json_node(payload, current_key=None)
        if not changed:
            return False

        path.write_text(json.dumps(patched, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.logger.info("Patched JSON: %s", path)
        return True

    def _patch_json_node(self, node: Any, current_key: str | None) -> tuple[Any, bool]:
        """Recursively patch JSON nodes."""

        changed = False
        if isinstance(node, dict):
            updated: Dict[str, Any] = {}
            for key, value in node.items():
                new_key = self._replace_text(key)
                new_value, value_changed = self._patch_json_node(value, current_key=key)
                new_value, value_changed_2 = self._patch_special_dict_value(new_value, key)
                changed = changed or new_key != key or value_changed or value_changed_2
                updated[new_key] = new_value
            return updated, changed

        if isinstance(node, list):
            updated_list: List[Any] = []
            for item in node:
                new_item, item_changed = self._patch_json_node(item, current_key=current_key)
                changed = changed or item_changed
                updated_list.append(new_item)
            return updated_list, changed

        if isinstance(node, str):
            new_value = self._replace_text(node)
            return new_value, new_value != node

        return node, False

    def _patch_special_dict_value(self, value: Any, key: str) -> tuple[Any, bool]:
        """Patch numeric fields and layer metadata when the surrounding key indicates it."""

        if isinstance(value, (int, float)):
            normalized = key.lower()
            for field_name, replacement in self.profile.numeric_field_defaults.items():
                if field_name in normalized:
                    if value != replacement:
                        return replacement, True
                    return value, False
            return value, False

        if isinstance(value, str):
            normalized_key = key.lower()
            if normalized_key in {"name", "layer_name", "layer"}:
                mapped = self.profile.abstract_layer_name_aliases.get(value, value)
                mapped = self._replace_text(mapped)
                return mapped, mapped != value

        if isinstance(value, dict):
            changed = False
            mapped_value = dict(value)
            for key_name in ("name", "layer_name"):
                if key_name in mapped_value and isinstance(mapped_value[key_name], str):
                    original = mapped_value[key_name]
                    mapped = self.profile.abstract_layer_name_aliases.get(original, original)
                    mapped = self._replace_text(mapped)
                    if mapped != original:
                        mapped_value[key_name] = mapped
                        changed = True

            if "layer" in mapped_value and "datatype" in mapped_value and isinstance(mapped_value.get("name"), str):
                layer_name = self.profile.abstract_layer_name_aliases.get(mapped_value["name"], mapped_value["name"])
                gds_ids = self.profile.abstract_layer_ids.get(layer_name)
                if gds_ids is not None:
                    if mapped_value["layer"] != gds_ids[0]:
                        mapped_value["layer"] = gds_ids[0]
                        changed = True
                    if mapped_value["datatype"] != gds_ids[1]:
                        mapped_value["datatype"] = gds_ids[1]
                        changed = True

            return mapped_value, changed

        return value, False

    def _replace_text(self, text: str) -> str:
        """Apply string-level SKY130 -> GF180MCU substitutions."""

        result = text
        for old, new in self.profile.sky130_to_gf180_models.items():
            result = re.sub(rf"\b{re.escape(old)}\b", new, result)
        result = re.sub(r"\bsky130A\b", "gf180mcu", result)
        result = re.sub(r"\bsky130\b", "gf180mcu", result)
        result = re.sub(r"\bsky130_fd_pr__\b", "gf180mcu_fd_pr__", result)
        return result

    # ---------------------------------------------------------------------
    # SPICE translation
    # ---------------------------------------------------------------------
    def translate_netlist(self, input_netlist: Path | str, output_path: Path | None = None) -> Path:
        """Translate SKY130 primitive device names to GF180MCU equivalents."""

        input_path = Path(input_netlist).expanduser().resolve()
        if not input_path.is_file():
            raise NetlistTranslationError(f"netlist not found: {input_path}")

        output_path = output_path or input_path.with_name(f"{input_path.stem}_gf180.sp")
        output_path = Path(output_path).expanduser().resolve()

        text = input_path.read_text(encoding="utf-8", errors="ignore")
        translated = self._translate_spice_text(text)
        output_path.write_text(translated, encoding="utf-8")
        self.logger.info("Wrote translated netlist: %s", output_path)
        return output_path

    def _translate_spice_text(self, text: str) -> str:
        """Regex-based translator for legacy SKY130 primitive devices."""

        translated = text
        for sky130_model, gf180_model in self.profile.sky130_to_gf180_models.items():
            translated = re.sub(rf"\b{re.escape(sky130_model)}\b", gf180_model, translated)
        return translated

    # ---------------------------------------------------------------------
    # ALIGN CLI wrapper
    # ---------------------------------------------------------------------
    def locate_schematic2layout(self, explicit: Path | str | None = None) -> Path:
        """Locate ALIGN's ``schematic2layout.py`` entry point."""

        if explicit is not None:
            script = Path(explicit).expanduser().resolve()
            if script.is_file():
                return script
            raise FileNotFoundError(f"schematic2layout.py not found: {script}")

        env_candidates = [
            os.environ.get("ALIGN_SCHEMATIC2LAYOUT"),
            os.environ.get("ALIGN_HOME"),
            os.environ.get("ALIGN_ROOT"),
            os.environ.get("ALIGN_PATH"),
        ]
        for candidate in env_candidates:
            if not candidate:
                continue
            root = Path(candidate).expanduser()
            if root.is_file() and root.name == "schematic2layout.py":
                return root.resolve()
            if root.is_dir():
                found = self._search_for_schematic2layout(root)
                if found is not None:
                    return found

        for base in self._common_search_bases():
            found = self._search_for_schematic2layout(base)
            if found is not None:
                return found

        which = shutil.which("schematic2layout.py")
        if which:
            return Path(which).resolve()

        raise FileNotFoundError(
            "Unable to locate ALIGN's schematic2layout.py. "
            "Pass --schematic2layout or set ALIGN_SCHEMATIC2LAYOUT."
        )

    def _search_for_schematic2layout(self, root: Path) -> Path | None:
        direct_candidates = [
            root / "schematic2layout.py",
            root / "bin" / "schematic2layout.py",
            root / "scripts" / "schematic2layout.py",
            root / "ALIGN" / "schematic2layout.py",
        ]
        for candidate in direct_candidates:
            if candidate.is_file():
                return candidate.resolve()
        try:
            for candidate in root.rglob("schematic2layout.py"):
                if candidate.is_file():
                    return candidate.resolve()
        except OSError:
            return None
        return None

    def run_schematic2layout(
        self,
        translated_netlist: Path | str,
        top_subckt: str,
        gf180_pdk_dir: Path | str,
        schematic2layout_py: Path | str | None = None,
        extra_args: Sequence[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Execute ALIGN's CLI and provide verbose errors on failure."""

        netlist_path = Path(translated_netlist).expanduser().resolve()
        pdk_dir = Path(gf180_pdk_dir).expanduser().resolve()
        if not netlist_path.is_file():
            raise FileNotFoundError(f"translated netlist does not exist: {netlist_path}")
        if not pdk_dir.is_dir():
            raise FileNotFoundError(f"GF180 PDK directory does not exist: {pdk_dir}")

        script = self.locate_schematic2layout(schematic2layout_py)
        python_exe = sys.executable or "python"
        command = [
            python_exe,
            str(script),
            "--netlist",
            str(netlist_path),
            "--subckt",
            top_subckt,
            "--pdk_root",
            str(pdk_dir),
        ]
        if extra_args:
            command.extend(list(extra_args))

        self.logger.info("Running ALIGN command: %s", " ".join(command))
        try:
            proc = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if stdout:
                print(stdout, file=sys.stdout)
            if stderr:
                print(stderr, file=sys.stderr)
            raise AlignCommandError(
                f"ALIGN schematic2layout.py failed with return code {exc.returncode}",
                returncode=exc.returncode,
                stdout=stdout,
                stderr=stderr,
                command=command,
            ) from exc

        if proc.stdout:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.stderr:
            print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
        return proc

    # ---------------------------------------------------------------------
    # High-level orchestration
    # ---------------------------------------------------------------------
    def prepare_gf180_pdk(
        self,
        pdk_root: Path | str | None = None,
        source_name: str = "sky130",
    ) -> Tuple[Path, Path]:
        """Clone and patch the GF180MCU PDK tree.

        Returns:
            A pair of ``(source_pdk_dir, gf180_pdk_dir)``.
        """

        root = self.resolve_align_pdk_root(pdk_root)
        source_dir = self.find_source_pdk_dir(root, source_name=source_name)
        gf180_dir = self.clone_sky130_to_gf180(root, source_name=source_name)
        self.patch_gf180_pdk_jsons(gf180_dir)
        return source_dir, gf180_dir

    def run_end_to_end(
        self,
        netlist_path: Path | str,
        top_subckt: str,
        pdk_root: Path | str | None = None,
        source_name: str = "sky130",
        schematic2layout_py: Path | str | None = None,
        extra_args: Sequence[str] | None = None,
    ) -> WrapperRunResult:
        """Perform the complete migrate -> translate -> execute flow."""

        root = self.resolve_align_pdk_root(pdk_root)
        source_dir, gf180_dir = self.prepare_gf180_pdk(root, source_name=source_name)
        translated = self.translate_netlist(netlist_path)
        proc = self.run_schematic2layout(
            translated,
            top_subckt,
            gf180_dir,
            schematic2layout_py=schematic2layout_py,
            extra_args=extra_args,
        )
        return WrapperRunResult(
            pdk_root=root,
            source_pdk_dir=source_dir,
            gf180_pdk_dir=gf180_dir,
            translated_netlist=translated,
            cli_stdout=proc.stdout,
            cli_stderr=proc.stderr,
        )


# -------------------------------------------------------------------------
# Demo/test harness helpers
# -------------------------------------------------------------------------
def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _create_mock_sky130_tree(workspace: Path) -> Path:
    """Create a small mock SKY130 tree with dummy ALIGN JSON files."""

    sky130_root = workspace / "mock_align_pdk" / "sky130"
    align_dir = sky130_root / "libs.tech" / "align"

    layers_json = {
        "technology": "sky130",
        "manufacturing_grid": 0.001,
        "resolution": 0.001,
        "layers": [
            {"name": "sky130", "layer": 1, "datatype": 0},
            {"name": "sky130_fd_pr__nfet_01v8", "layer": 2, "datatype": 0},
            {"name": "sky130_fd_pr__pfet_01v8", "layer": 3, "datatype": 0},
        ],
    }
    min_width_rules_json = {
        "technology": "sky130A",
        "grid_pitch": 0.001,
        "rules": {
            "poly": {"min_width": 0.150},
            "metal1": {"min_width": 0.140},
            "metal2": {"min_width": 0.140},
        },
    }

    _write_text(align_dir / "layers.json", json.dumps(layers_json, indent=2))
    _write_text(align_dir / "min_width_rules.json", json.dumps(min_width_rules_json, indent=2))
    _write_text(
        align_dir / "other_rules.json",
        json.dumps({"label": "sky130 legacy placeholder", "model": "sky130_fd_pr__nfet_01v8"}),
    )

    # Add a second sky130A-style folder so the discovery logic has real-world
    # naming to choose from during the demo.
    sky130a_root = workspace / "mock_align_pdk" / "sky130A"
    shutil.copytree(sky130_root, sky130a_root)
    return sky130_root.parent


def _create_mock_netlist(workspace: Path, topcell: str) -> Path:
    """Create a small SPICE netlist that exercises the regex translator."""

    netlist = workspace / "sample_input.sp"
    _write_text(
        netlist,
        "\n".join(
            [
                "* Mock netlist exported from a schematic editor",
                f".subckt {topcell} D G S B VDD VSS",
                "XMN0 D G S B sky130_fd_pr__nfet_01v8 W=1.5u L=0.15u",
                "XMP0 D G VDD VDD sky130_fd_pr__pfet_01v8 W=3u L=0.15u",
                ".ends {topcell}",
                "",
            ]
        ).format(topcell=topcell),
    )
    return netlist


def _create_mock_schematic2layout(workspace: Path) -> Path:
    """Create a tiny ALIGN CLI stand-in for integration testing."""

    script = workspace / "mock_align" / "schematic2layout.py"
    _write_text(
        script,
        "\n".join(
            [
                "from __future__ import annotations",
                "import argparse",
                "from pathlib import Path",
                "",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--netlist', required=True)",
                "parser.add_argument('--subckt', required=True)",
                "parser.add_argument('--pdk_root', required=True)",
                "args = parser.parse_args()",
                "netlist = Path(args.netlist)",
                "print(f'ALIGN mock schematic2layout received: {netlist.name} / {args.subckt} / {args.pdk_root}')",
                "print(f'NETLIST_EXISTS={netlist.is_file()}')",
            ]
        )
        + "\n",
    )
    return script


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ALIGN-GF180 Wrapper demo harness")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Optional workspace directory for mock artifacts. Defaults to a temp directory.",
    )
    parser.add_argument(
        "--pdk-root",
        type=Path,
        default=None,
        help="Explicit ALIGN PDK root. If omitted in demo mode, a mock SKY130 tree is created.",
    )
    parser.add_argument(
        "--source-pdk-name",
        default="sky130",
        help="Source PDK directory name to clone from inside the ALIGN PDK root.",
    )
    parser.add_argument(
        "--netlist",
        type=Path,
        default=None,
        help="Input SPICE netlist to translate. If omitted in demo mode, a mock file is created.",
    )
    parser.add_argument(
        "--topcell",
        default="demo_top",
        help="Top subcircuit name to pass to schematic2layout.py.",
    )
    parser.add_argument(
        "--schematic2layout",
        type=Path,
        default=None,
        help="Explicit path to ALIGN's schematic2layout.py. If omitted in demo mode, a mock script is created.",
    )
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Optional extra CLI arguments forwarded to schematic2layout.py. May be repeated.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Force creation of mock SKY130 data and a mock ALIGN CLI for end-to-end testing.",
    )
    return parser


def _run_demo_or_real(args: argparse.Namespace) -> int:
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    wrapper = AlignGf180Wrapper()

    if args.workspace is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="align_gf180_wrapper_")
        workspace = Path(tmp_ctx.name)
    else:
        tmp_ctx = None
        workspace = args.workspace.expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)

    try:
        demo_mode = args.demo or args.pdk_root is None or args.netlist is None or args.schematic2layout is None

        if demo_mode:
            pdk_root = _create_mock_sky130_tree(workspace)
            netlist = _create_mock_netlist(workspace, args.topcell)
            schematic2layout = _create_mock_schematic2layout(workspace)
        else:
            pdk_root = args.pdk_root.expanduser().resolve()
            netlist = args.netlist.expanduser().resolve()
            schematic2layout = args.schematic2layout.expanduser().resolve() if args.schematic2layout else None

        source_dir, gf180_dir = wrapper.prepare_gf180_pdk(
            pdk_root=pdk_root,
            source_name=args.source_pdk_name,
        )
        translated = wrapper.translate_netlist(netlist)

        proc = wrapper.run_schematic2layout(
            translated,
            args.topcell,
            gf180_dir,
            schematic2layout_py=schematic2layout,
            extra_args=args.extra_arg,
        )

        print("\n--- Summary ---")
        print(f"Workspace: {workspace}")
        print(f"Source PDK: {source_dir}")
        print(f"GF180 PDK: {gf180_dir}")
        print(f"Translated netlist: {translated}")
        print("schematic2layout return code: 0")
        if proc.stdout:
            print("--- CLI stdout ---")
            print(proc.stdout.rstrip())
        if proc.stderr:
            print("--- CLI stderr ---")
            print(proc.stderr.rstrip())
        return 0
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_argument_parser().parse_args(argv)
    return _run_demo_or_real(args)


if __name__ == "__main__":
    raise SystemExit(main())
