#!/usr/bin/env python3
"""Generate deterministic input/output activity for the routed nine-term convolution primitive."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


WEIGHTS = [0x600, -0x300, 0x900, 0x1200, 0x800, -0x500, 0x400, 0xB00, 0x700]


def main() -> None:
    out = Path("artifacts/ASIC_XL/primitive_characterization/convolution_synapse_9term").resolve()
    out.mkdir(parents=True, exist_ok=True)
    vcd = out / "conv9_activity.vcd"
    lfsr = 0x12D
    samples: list[dict[str, int]] = []
    with vcd.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("$date deterministic $end\n$version EventSpikeSeg conv9 trace $end\n")
        handle.write("$timescale 1ps $end\n$scope module conv9_activity_tb $end\n")
        handle.write("$scope module dut $end\n")
        handle.write("$var wire 1 ! clk $end\n")
        handle.write("$var wire 9 \" spike_vector_i [8:0] $end\n")
        handle.write("$var wire 32 # current_delta_o [31:0] $end\n")
        handle.write("$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        for index in range(128):
            lfsr = ((lfsr << 1) | (((lfsr >> 8) ^ (lfsr >> 4)) & 1)) & 0x1FF
            value = sum(weight for bit, weight in enumerate(WEIGHTS) if (lfsr >> bit) & 1)
            stamp = index * 5_000
            handle.write(f"#{stamp}\n0!\nb{lfsr:09b} \"\nb{value & 0xffffffff:032b} #\n")
            handle.write(f"#{stamp + 2_500}\n1!\n")
            samples.append({"spikes": lfsr, "current_delta": value})
    manifest = {
        "scope": "one_fully_connected_3x3_convolution_output_nine_hardwired_terms",
        "samples": len(samples),
        "trace_duration_ns": 640.0,
        "term_count": 9,
        "vcd_sha256": hashlib.sha256(vcd.read_bytes()).hexdigest(),
        "claim_limit": "normalize by nine terms; actor-level adder and routing effects remain configuration-dependent",
    }
    (out / "activity_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
