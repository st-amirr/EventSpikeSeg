#!/usr/bin/env python3
"""Generate and verify an RTL VCD for the exact XL enc3.pointwise trace."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from eventspikeseg.asic.activity_trace import sha256_file, validate_trace_payload

ROOT = Path(__file__).resolve().parents[1]
ACTOR = "enc3.pointwise"


def assert_cocotb_results_passed(results_path: Path) -> None:
    """Reject missing, empty, failed, or errored cocotb JUnit results."""

    if not results_path.is_file():
        raise RuntimeError(f"cocotb did not produce {results_path}")
    root = ET.parse(results_path).getroot()
    testcases = root.findall(".//testcase")
    failures = root.findall(".//failure")
    errors = root.findall(".//error")
    if not testcases or failures or errors:
        raise RuntimeError(
            "cocotb verification failed: "
            f"testcases={len(testcases)}, failures={len(failures)}, "
            f"errors={len(errors)}; see {results_path}"
        )


def validate_trace(
    trace_path: Path, model_spec: Path, checkpoint: Path, event_file: Path
) -> dict:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    validate_trace_payload(trace)
    expected = {
        "actor": ACTOR,
        "model_spec_sha256": sha256_file(model_spec),
        "checkpoint_sha256": sha256_file(checkpoint),
        "event_file_sha256": sha256_file(event_file),
    }
    observed = {key: trace.get(key) for key in expected}
    if observed != expected:
        raise ValueError(
            f"actor trace provenance mismatch: expected={expected}, observed={observed}"
        )
    if trace.get("scope") != "single_coordinate_checkpoint_exact_integer_actor_trace":
        raise ValueError("actor trace does not have the required exact single-coordinate scope")
    if int(trace.get("bins", 0)) != 10:
        raise ValueError("XL activity capture requires the complete ten-bin trace")
    return trace


def main() -> None:
    from cocotb.runner import get_runner

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--export", type=Path, default=Path("artifacts/ASIC_XL"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--event-file", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ASIC_XL/activity/enc3_pointwise_1x1"),
    )
    args = parser.parse_args()
    model_spec = args.export / "model_spec.yaml"
    validate_trace(args.trace, model_spec, args.checkpoint, args.event_file)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_top = output_dir / "enc3_pointwise_1x1_activity_top.sv"
    try:
        from scripts.generate_resident_tile_pnr_top import generate_tile_top
    except ModuleNotFoundError:
        from generate_resident_tile_pnr_top import generate_tile_top

    generate_tile_top(model_spec, generated_top, actor_name=ACTOR, tile_width=1, tile_height=1)
    sources = [
        ROOT / "asic/rtl/resident_convolution_synapses.sv",
        ROOT / "asic/rtl/resident_plif_population.sv",
        ROOT / "asic/rtl/retinotopic_mechanism_update.sv",
        ROOT / "asic/rtl/resident_retinotopic_plif_population.sv",
        ROOT / "asic/rtl/resident_channelized_plif_actor.sv",
        generated_top,
        ROOT / "verification/cocotb/xl_actor_activity_vcd_tb.sv",
    ]
    runner = get_runner("icarus")
    runner.build(
        verilog_sources=sources,
        hdl_toplevel="xl_actor_activity_vcd_tb",
        build_dir=output_dir / "sim_build",
        always=True,
        build_args=["-g2012"],
    )
    shutil.copy2(
        ROOT / "verification/cocotb/test_xl_actor_activity_vcd.py",
        output_dir / "test_xl_actor_activity_vcd.py",
    )
    environment = dict(os.environ)
    environment["EVENTSPIKESEG_ACTOR_TRACE"] = str(args.trace.resolve())
    results = output_dir / "results.xml"
    results.unlink(missing_ok=True)
    runner.test(
        hdl_toplevel="xl_actor_activity_vcd_tb",
        test_module="test_xl_actor_activity_vcd",
        test_dir=output_dir,
        extra_env=environment,
    )
    assert_cocotb_results_passed(results)
    vcd = output_dir / "enc3_pointwise_1x1_activity.vcd"
    if not vcd.is_file() or vcd.stat().st_size == 0:
        raise RuntimeError(f"simulation passed without producing {vcd}")
    print(f"verified exact actor VCD: {vcd} ({vcd.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
