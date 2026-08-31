#!/usr/bin/env python3
"""Generate a revision-pinned predictive ASAP7 FakeRAM macro catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _required(pattern: str, text: str, source: Path) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"missing {pattern!r} in {source}")
    return match.group(1)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_macro(liberty_path: Path, lef_path: Path, platform_dir: Path) -> dict[str, Any]:
    liberty = liberty_path.read_text(encoding="utf-8")
    lef = lef_path.read_text(encoding="utf-8")
    name = _required(r"^cell\(([^)]+)\)", liberty, liberty_path)
    lef_name = _required(r"^MACRO\s+(\S+)", lef, lef_path)
    if name != lef_name:
        raise ValueError(f"Liberty/LEF macro mismatch: {name} != {lef_name}")
    width = int(_required(r"word_width\s*:\s*(\d+)\s*;", liberty, liberty_path))
    address_width = int(
        _required(r"address_width\s*:\s*(\d+)\s*;", liberty, liberty_path)
    )
    lef_width = float(_required(r"^\s*SIZE\s+([0-9.]+)\s+BY", lef, lef_path))
    lef_height = float(_required(r"^\s*SIZE\s+[0-9.]+\s+BY\s+([0-9.]+)", lef, lef_path))
    area = float(_required(r"^\s*area\s*:\s*([0-9.]+)\s*;", liberty, liberty_path))
    leakage = float(
        _required(r"^\s*cell_leakage_power\s*:\s*([0-9.]+)\s*;", liberty, liberty_path)
    )
    min_period = float(
        _required(r"^\s*min_period\s*:\s*([0-9.]+)\s*;", liberty, liberty_path)
    )
    return {
        "name": name,
        "ports": "1RW",
        "word_bits": width,
        "depth": 1 << address_width,
        "read_latency_cycles": 1,
        "area_um2": area,
        "lef_width_um": lef_width,
        "lef_height_um": lef_height,
        "leakage_uW": leakage,
        "minimum_clock_period_ns": min_period,
        "liberty": str(liberty_path.relative_to(platform_dir)),
        "lef": str(lef_path.relative_to(platform_dir)),
        "liberty_sha256": _sha256(liberty_path),
        "lef_sha256": _sha256(lef_path),
    }


def generate_catalog(orfs_root: Path, source_revision: str | None = None) -> dict[str, Any]:
    root = orfs_root.resolve()
    platform = root / "flow/platforms/asap7"
    lib_dir = platform / "lib/NLDM"
    macros = []
    for liberty_path in sorted(lib_dir.glob("fakeram*.lib")):
        lef_path = platform / "lef" / f"{liberty_path.stem}.lef"
        if lef_path.exists():
            macros.append(parse_macro(liberty_path, lef_path, platform))
    if not macros:
        raise ValueError(f"no paired ASAP7 FakeRAM Liberty/LEF views under {platform}")
    revision = source_revision
    if revision is None:
        revision = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("source revision must be a full 40-character Git SHA")
    return {
        "format": "eventspikeseg-sram-catalog-v2",
        "catalog": f"ORFS-ASAP7-FakeRAM-{revision[:12]}",
        "source": "OpenROAD-flow-scripts ASAP7 FakeRAM2.0 predictive models",
        "source_url": "https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts",
        "source_revision": revision,
        "process": "ASAP7 predictive 7nm",
        "nominal_voltage_V": 0.7,
        "nominal_temperature_C": 25,
        "ports": "1RW",
        "selection_objective": "minimum_area",
        "characterized": True,
        "characterization_kind": "predictive_model",
        "silicon_characterized": False,
        "research_PPA_eligible": True,
        "tapeout_signoff_eligible": False,
        "macros": macros,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("orfs_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    catalog = generate_catalog(args.orfs_root, args.source_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
