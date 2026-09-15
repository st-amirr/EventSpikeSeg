#!/usr/bin/env python3
"""Generate every exact reusable resident-actor hard-macro RTL variant."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.generate_resident_tile_pnr_top import (
        exact_tile_geometry,
        exact_tile_variant_key,
        generate_tile_top,
    )
except ModuleNotFoundError:  # Direct execution adds scripts/, not the repository root.
    from generate_resident_tile_pnr_top import (  # type: ignore[no-redef]
        exact_tile_geometry,
        exact_tile_variant_key,
        generate_tile_top,
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _slug(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return result or "variant"


def collect_variants(
    model_spec_path: Path,
    *,
    tile_width: int = 8,
    tile_height: int = 8,
) -> list[dict[str, Any]]:
    """Collect one representative coordinate for every exact macro topology."""
    spec = json.loads(model_spec_path.read_text(encoding="utf-8"))
    actor_order = [str(name) for name in spec["graph"]["actor_topological_order"]]
    layers = {str(layer["name"]): layer for layer in spec["layers"]}
    result: list[dict[str, Any]] = []
    for actor_name in actor_order:
        layer = layers[actor_name]
        output_height, output_width = (int(value) for value in layer["output_hw"])
        tile_columns = math.ceil(output_width / tile_width)
        tile_rows = math.ceil(output_height / tile_height)
        variants: dict[str, dict[str, Any]] = {}
        for tile_row in range(tile_rows):
            for tile_column in range(tile_columns):
                geometry = exact_tile_geometry(
                    layer,
                    tile_width=tile_width,
                    tile_height=tile_height,
                    tile_column=tile_column,
                    tile_row=tile_row,
                )
                key = exact_tile_variant_key(geometry)
                if key not in variants:
                    variants[key] = {
                        "actor": actor_name,
                        "variant": key,
                        "instance_count": 0,
                        "representative_tile": {
                            "column": tile_column,
                            "row": tile_row,
                        },
                        "geometry": geometry,
                    }
                variants[key]["instance_count"] += 1
        result.extend(variants[key] for key in sorted(variants))
    return result


def _validate_plan(
    variants: list[dict[str, Any]],
    plan_path: Path,
    *,
    tile_width: int,
    tile_height: int,
) -> str:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if list(plan["tile_nominal_hw"]) != [tile_height, tile_width]:
        raise ValueError("tile plan nominal dimensions do not match generation request")
    expected = {
        (str(actor["name"]), str(key)): int(count)
        for actor in plan["actors"]
        for key, count in actor["exact_macro_variant_counts"].items()
    }
    actual = {
        (str(item["actor"]), str(item["variant"])): int(item["instance_count"])
        for item in variants
    }
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        wrong = sorted(
            key for key in set(actual) & set(expected) if actual[key] != expected[key]
        )
        raise ValueError(
            "tile plan does not match exact macro enumeration: "
            f"missing={missing[:3]}, extra={extra[:3]}, wrong_counts={wrong[:3]}"
        )
    return _sha256_file(plan_path)


def generate_variants(
    model_spec_path: Path,
    output_dir: Path,
    *,
    tile_width: int = 8,
    tile_height: int = 8,
    plan_path: Path | None = None,
) -> dict[str, Any]:
    if tile_width < 1 or tile_height < 1:
        raise ValueError("tile dimensions must be positive")
    model_spec_path = model_spec_path.resolve()
    output_dir = output_dir.resolve()
    variants = collect_variants(
        model_spec_path, tile_width=tile_width, tile_height=tile_height
    )
    plan_sha256 = None
    if plan_path is not None:
        plan_path = plan_path.resolve()
        plan_sha256 = _validate_plan(
            variants,
            plan_path,
            tile_width=tile_width,
            tile_height=tile_height,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    generated = 0
    reused = 0
    manifest_variants: list[dict[str, Any]] = []
    for item in variants:
        identity = f"{item['actor']}\0{item['variant']}"
        suffix = _sha256_bytes(identity.encode("utf-8"))[:12]
        module_name = f"resident_macro_{_slug(str(item['actor']))}_{suffix}"
        relative_path = Path(_slug(str(item["actor"]))) / f"{module_name}.sv"
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        representative = item["representative_tile"]
        try:
            generate_tile_top(
                model_spec_path,
                temporary,
                actor_name=str(item["actor"]),
                tile_width=tile_width,
                tile_height=tile_height,
                tile_column=int(representative["column"]),
                tile_row=int(representative["row"]),
                module_name=module_name,
            )
            payload = temporary.read_bytes()
            if target.exists() and target.read_bytes() == payload:
                reused += 1
                temporary.unlink()
            else:
                temporary.replace(target)
                generated += 1
        finally:
            if temporary.exists():
                temporary.unlink()
        manifest_variants.append(
            {
                **item,
                "module": module_name,
                "rtl": relative_path.as_posix(),
                "rtl_sha256": _sha256_file(target),
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "architecture": "exact_reusable_resident_actor_hard_macros",
        "model_spec": str(model_spec_path),
        "model_spec_sha256": _sha256_file(model_spec_path),
        "resident_tile_plan": str(plan_path) if plan_path is not None else None,
        "resident_tile_plan_sha256": plan_sha256,
        "tile_nominal_hw": [tile_height, tile_width],
        "macro_variant_count": len(manifest_variants),
        "logical_tile_instance_count": sum(
            int(item["instance_count"]) for item in manifest_variants
        ),
        "generated_rtl_count": generated,
        "reused_rtl_count": reused,
        "variants": manifest_variants,
    }
    manifest_path = output_dir / "manifest.json"
    temporary_manifest = output_dir / f".manifest.json.{os.getpid()}.tmp"
    temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_spec", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--tile-width", type=int, default=8)
    parser.add_argument("--tile-height", type=int, default=8)
    parser.add_argument("--tile-plan", type=Path)
    args = parser.parse_args()
    manifest = generate_variants(
        args.model_spec,
        args.output_dir,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        plan_path=args.tile_plan,
    )
    print(
        json.dumps(
            {
                key: manifest[key]
                for key in (
                    "macro_variant_count",
                    "logical_tile_instance_count",
                    "generated_rtl_count",
                    "reused_rtl_count",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
