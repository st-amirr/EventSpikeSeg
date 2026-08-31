#!/usr/bin/env python3
"""Tile logical EventSpikeSeg SRAM requests onto a supplied macro catalog."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def plan_banking(manifest: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    planned = []
    for bank in manifest["banks"]:
        required_ports = str(bank["ports"])
        macros = [
            macro for macro in catalog["macros"]
            if str(macro.get("ports")) == required_ports
        ]
        if not macros:
            raise ValueError(f"catalog contains no {required_ports} macros")
        candidates = []
        for macro in macros:
            macro_width = int(macro["word_bits"])
            macro_depth = int(macro["depth"])
            width_tiles = math.ceil(int(bank["word_bits"]) / macro_width)
            depth_tiles = math.ceil(int(bank["depth"]) / macro_depth)
            logical_instances = int(bank["instances"])
            physical_instances = logical_instances * width_tiles * depth_tiles
            allocated_bits = physical_instances * macro_width * macro_depth
            candidate = {
                    "macro": str(macro["name"]),
                    "width_tiles": width_tiles,
                    "depth_tiles": depth_tiles,
                    "physical_instances": physical_instances,
                    "allocated_bits": allocated_bits,
                    "wasted_bits": allocated_bits - int(bank["total_bits"]),
                }
            if "area_um2" in macro:
                candidate["macro_area_um2"] = float(macro["area_um2"])
                candidate["total_area_um2"] = (
                    physical_instances * float(macro["area_um2"])
                )
            if "leakage_uW" in macro:
                candidate["macro_leakage_uW"] = float(macro["leakage_uW"])
                candidate["total_leakage_uW"] = (
                    physical_instances * float(macro["leakage_uW"])
                )
            if "minimum_clock_period_ns" in macro:
                candidate["minimum_clock_period_ns"] = float(
                    macro["minimum_clock_period_ns"]
                )
            candidates.append(candidate)
        objective = str(catalog.get("selection_objective", "minimum_allocated_bits"))
        if objective == "minimum_area":
            if not all("total_area_um2" in item for item in candidates):
                raise ValueError("minimum_area catalog has macro without area_um2")
            choice = min(
                candidates,
                key=lambda item: (
                    item["total_area_um2"], item["allocated_bits"],
                    item["physical_instances"], item["macro"],
                ),
            )
        elif objective == "minimum_allocated_bits":
            choice = min(
                candidates,
                key=lambda item: (
                    item["allocated_bits"], item["physical_instances"], item["macro"],
                ),
            )
        else:
            raise ValueError(f"unsupported selection objective {objective}")
        planned.append({**bank, **choice})
    logical_bits = sum(int(item["total_bits"]) for item in planned)
    allocated_bits = sum(int(item["allocated_bits"]) for item in planned)
    return {
        "format": "eventspikeseg-sram-banking-plan-v1",
        "source_manifest_format": manifest["format"],
        "catalog": catalog.get("catalog", "unnamed"),
        "characterized": bool(catalog.get("characterized", False)),
        "characterization_kind": catalog.get("characterization_kind", "unspecified"),
        "silicon_characterized": bool(catalog.get("silicon_characterized", False)),
        "research_PPA_eligible": bool(catalog.get("research_PPA_eligible", False)),
        "tapeout_signoff_eligible": bool(catalog.get("tapeout_signoff_eligible", False)),
        "selection_objective": catalog.get("selection_objective", "minimum_allocated_bits"),
        "banks": planned,
        "totals": {
            "logical_bits": logical_bits,
            "allocated_bits": allocated_bits,
            "wasted_bits": allocated_bits - logical_bits,
            "utilization": logical_bits / allocated_bits,
            "physical_macro_instances": sum(
                int(item["physical_instances"]) for item in planned
            ),
            "macro_area_um2": sum(float(item.get("total_area_um2", 0.0))
                                  for item in planned),
            "macro_area_mm2": sum(float(item.get("total_area_um2", 0.0))
                                  for item in planned) / 1_000_000,
            "macro_leakage_uW": sum(float(item.get("total_leakage_uW", 0.0))
                                    for item in planned),
        },
        "PPA_eligible": bool(catalog.get("research_PPA_eligible", False)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    plan = plan_banking(manifest, catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
