#!/usr/bin/env python3
"""Tile logical EventSpikeSeg SRAM requests onto a supplied macro catalog."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def plan_banking(manifest: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    macros = [macro for macro in catalog["macros"] if macro.get("ports") == "1R1W"]
    if not macros:
        raise ValueError("catalog contains no 1R1W macros")
    planned = []
    for bank in manifest["banks"]:
        candidates = []
        for macro in macros:
            macro_width = int(macro["word_bits"])
            macro_depth = int(macro["depth"])
            width_tiles = math.ceil(int(bank["word_bits"]) / macro_width)
            depth_tiles = math.ceil(int(bank["depth"]) / macro_depth)
            logical_instances = int(bank["instances"])
            physical_instances = logical_instances * width_tiles * depth_tiles
            allocated_bits = physical_instances * macro_width * macro_depth
            candidates.append(
                {
                    "macro": str(macro["name"]),
                    "width_tiles": width_tiles,
                    "depth_tiles": depth_tiles,
                    "physical_instances": physical_instances,
                    "allocated_bits": allocated_bits,
                    "wasted_bits": allocated_bits - int(bank["total_bits"]),
                }
            )
        choice = min(candidates, key=lambda item: (item["allocated_bits"],
                                                   item["physical_instances"],
                                                   item["macro"]))
        planned.append({**bank, **choice})
    logical_bits = sum(int(item["total_bits"]) for item in planned)
    allocated_bits = sum(int(item["allocated_bits"]) for item in planned)
    return {
        "format": "eventspikeseg-sram-banking-plan-v1",
        "source_manifest_format": manifest["format"],
        "catalog": catalog.get("catalog", "unnamed"),
        "characterized": bool(catalog.get("characterized", False)),
        "banks": planned,
        "totals": {
            "logical_bits": logical_bits,
            "allocated_bits": allocated_bits,
            "wasted_bits": allocated_bits - logical_bits,
            "utilization": logical_bits / allocated_bits,
            "physical_macro_instances": sum(
                int(item["physical_instances"]) for item in planned
            ),
        },
        "PPA_eligible": bool(catalog.get("characterized", False)),
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
