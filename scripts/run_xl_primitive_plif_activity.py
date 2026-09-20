#!/usr/bin/env python3
"""Generate a deterministic ten-bin activity trace for one routed PLIF cell."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PERIOD_PS = 5_000
SIGNALS = {
    "!": ("clk", 1),
    '"': ("reset", 1),
    "#": ("contribution_valid_i", 1),
    "$": ("weight_i", 24),
    "%": ("dense_current_valid_i", 1),
    "&": ("dense_current_delta_i", 32),
    "'": ("completion_valid_i", 1),
    "(": ("completion_tag_i", 24),
    ")": ("spike_ready_i", 1),
    "*": ("contribution_ready_o", 1),
    "+": ("dense_current_ready_o", 1),
    ",": ("completion_ready_o", 1),
    "-": ("spike_valid_o", 1),
    ".": ("spike_o", 1),
    "/": ("completion_tag_o", 24),
    "0": ("address_error_o", 1),
}


def signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


def bits(value: int, width: int) -> str:
    return format(value & ((1 << width) - 1), f"0{width}b")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("artifacts/ASIC_XL/primitive_characterization/ordinary_plif_1"),
    )
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    state = {name: 0 for name, _ in SIGNALS.values()}
    membrane = 0
    holding = False
    rows: list[dict] = []
    changes: list[tuple[int, dict[str, int]]] = []
    time_ps = 0

    def snapshot() -> None:
        changes.append((time_ps, dict(state)))

    def cycle(inputs: dict[str, int]) -> None:
        nonlocal time_ps, membrane, holding
        state.update(inputs)
        state["contribution_ready_o"] = int(not holding and not state["completion_valid_i"])
        state["dense_current_ready_o"] = int(not holding and not state["completion_valid_i"])
        state["completion_ready_o"] = int(not holding)
        state["spike_valid_o"] = int(holding)
        snapshot()
        time_ps += PERIOD_PS // 2
        state["clk"] = 1

        if state["reset"]:
            membrane = 0
            holding = False
            state["spike_o"] = 0
            state["completion_tag_o"] = 0
        elif holding:
            if state["spike_ready_i"]:
                holding = False
                state["spike_o"] = 0
        elif state["completion_valid_i"]:
            candidate = max(-(1 << 23), min((1 << 23) - 1, membrane))
            threshold = 0x008000
            spike = int(candidate >= threshold)
            committed = candidate - threshold if spike else candidate
            beta = signed(0x780000, 25)
            product = committed * beta
            membrane = ((product + (1 << 22)) >> 23) if product >= 0 else -(((-product) + (1 << 22)) >> 23)
            state["spike_o"] = spike
            state["completion_tag_o"] = state["completion_tag_i"]
            holding = True
        else:
            if state["dense_current_valid_i"]:
                membrane += signed(state["dense_current_delta_i"], 32)
            if state["contribution_valid_i"]:
                membrane += signed(state["weight_i"], 24)
            membrane = max(-(1 << 31), min((1 << 31) - 1, membrane))
        state["spike_valid_o"] = int(holding)
        snapshot()
        time_ps += PERIOD_PS // 2
        state["clk"] = 0

    snapshot()
    for _ in range(4):
        cycle({"reset": 1})
    cycle({"reset": 0})
    for bin_index in range(1, 11):
        w0 = (0x001200 + bin_index * 0x180) if bin_index % 3 else (-0x000700 - bin_index * 0x40)
        w1 = 0x000500 + bin_index * 0x60
        dense = (0x00000300 + bin_index * 0x40) if bin_index % 2 else 0
        before = membrane
        cycle({"contribution_valid_i": 1, "weight_i": w0})
        cycle({"contribution_valid_i": 1, "weight_i": w1})
        cycle({"contribution_valid_i": 0, "weight_i": 0,
               "dense_current_valid_i": int(bool(dense)), "dense_current_delta_i": dense})
        cycle({"dense_current_valid_i": 0, "dense_current_delta_i": 0,
               "completion_valid_i": 1, "completion_tag_i": bin_index})
        spike = state["spike_o"]
        after = membrane
        cycle({"completion_valid_i": 0, "spike_ready_i": 1})
        cycle({"spike_ready_i": 0})
        rows.append({"bin": bin_index, "membrane_before": before,
                     "weight_0": w0, "weight_1": w1, "dense_current": dense,
                     "spike": spike, "membrane_after_leak": after})

    vcd = out / "ordinary_plif_1_activity.vcd"
    with vcd.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("$date deterministic $end\n$version EventSpikeSeg PLIF trace $end\n")
        handle.write("$timescale 1ps $end\n$scope module plif_activity_tb $end\n")
        handle.write("$scope module dut $end\n")
        for code, (name, width) in SIGNALS.items():
            suffix = "" if width == 1 else f" [{width - 1}:0]"
            handle.write(f"$var wire {width} {code} {name}{suffix} $end\n")
        handle.write("$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        previous: dict[str, int] = {}
        for stamp, values in changes:
            handle.write(f"#{stamp}\n")
            for code, (name, width) in SIGNALS.items():
                value = values[name]
                if previous.get(name) == value:
                    continue
                handle.write(f"{value}{code}\n" if width == 1 else f"b{bits(value, width)} {code}\n")
                previous[name] = value

    manifest = {
        "scope": "one_ordinary_resident_plif_cell_synthetic_ten_bin_activity",
        "clock_period_ns": PERIOD_PS / 1000,
        "bins": 10,
        "cycles": time_ps // PERIOD_PS,
        "trace_duration_ns": time_ps / 1000,
        "vcd": str(vcd),
        "vcd_sha256": hashlib.sha256(vcd.read_bytes()).hexdigest(),
        "workload": rows,
        "claim_limit": "operational characterization of one ordinary PLIF cell; multiply by matching cell count and update rate",
    }
    (out / "activity_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("bins", "cycles", "trace_duration_ns", "vcd_sha256")}, indent=2))


if __name__ == "__main__":
    main()
