#!/usr/bin/env python3
"""Generate checkpoint-exact activity traces for isolated 140k ASIC primitives."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PERIOD_PS = 5_000
BETA = 0x712E2A
THRESHOLD = 0x005CD3
CONV_WEIGHTS = [0x00AC56, 0x0063B7, -0x002BBE, 0x099D95, 0x0BB3EC,
                0x0C709D, 0x10425D, 0x127FF6, 0x10AB56]
PLIF_SIGNALS = {
    "!": ("clk", 1), '"': ("reset", 1), "#": ("contribution_valid_i", 1),
    "$": ("weight_i", 24), "%": ("dense_current_valid_i", 1),
    "&": ("dense_current_delta_i", 32), "'": ("completion_valid_i", 1),
    "(": ("completion_tag_i", 24), ")": ("spike_ready_i", 1),
    "*": ("contribution_ready_o", 1), "+": ("dense_current_ready_o", 1),
    ",": ("completion_ready_o", 1), "-": ("spike_valid_o", 1),
    ".": ("spike_o", 1), "/": ("completion_tag_o", 24),
    "0": ("address_error_o", 1),
}


def signed(value: int, width: int) -> int:
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


def bits(value: int, width: int) -> str:
    return format(value & ((1 << width) - 1), f"0{width}b")


def write_plif(out: Path) -> dict:
    state = {name: 0 for name, _ in PLIF_SIGNALS.values()}
    membrane = 0
    holding = False
    time_ps = 0
    changes: list[tuple[int, dict[str, int]]] = []

    def snapshot() -> None:
        changes.append((time_ps, dict(state)))

    def cycle(inputs: dict[str, int]) -> None:
        nonlocal membrane, holding, time_ps
        state.update(inputs)
        state["contribution_ready_o"] = int(not holding and not state["completion_valid_i"])
        state["dense_current_ready_o"] = int(not holding and not state["completion_valid_i"])
        state["completion_ready_o"] = int(not holding)
        state["spike_valid_o"] = int(holding)
        snapshot(); time_ps += PERIOD_PS // 2; state["clk"] = 1
        if state["reset"]:
            membrane = 0; holding = False
            state["spike_o"] = 0; state["completion_tag_o"] = 0
        elif holding:
            if state["spike_ready_i"]:
                holding = False; state["spike_o"] = 0
        elif state["completion_valid_i"]:
            candidate = max(-(1 << 23), min((1 << 23) - 1, membrane))
            spike = int(candidate >= THRESHOLD)
            committed = candidate - THRESHOLD if spike else candidate
            product = committed * BETA
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
        snapshot(); time_ps += PERIOD_PS // 2; state["clk"] = 0

    snapshot()
    for _ in range(4): cycle({"reset": 1})
    cycle({"reset": 0})
    for index in range(1, 11):
        cycle({"contribution_valid_i": 1, "weight_i": CONV_WEIGHTS[(index - 1) % 9]})
        cycle({"contribution_valid_i": 1, "weight_i": CONV_WEIGHTS[index % 9]})
        dense = 0x300 + index * 0x40 if index % 2 else 0
        cycle({"contribution_valid_i": 0, "weight_i": 0,
               "dense_current_valid_i": int(bool(dense)), "dense_current_delta_i": dense})
        cycle({"dense_current_valid_i": 0, "dense_current_delta_i": 0,
               "completion_valid_i": 1, "completion_tag_i": index})
        cycle({"completion_valid_i": 0, "spike_ready_i": 1})
        cycle({"spike_ready_i": 0})

    path = out / "ordinary_plif_1_activity.vcd"
    with path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("$timescale 1ps $end\n$scope module plif140k_tb $end\n$scope module dut $end\n")
        for code, (name, width) in PLIF_SIGNALS.items():
            suffix = "" if width == 1 else f" [{width-1}:0]"
            handle.write(f"$var wire {width} {code} {name}{suffix} $end\n")
        handle.write("$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        previous: dict[str, int] = {}
        for stamp, values in changes:
            handle.write(f"#{stamp}\n")
            for code, (name, width) in PLIF_SIGNALS.items():
                if previous.get(name) == values[name]: continue
                handle.write(f"{values[name]}{code}\n" if width == 1 else f"b{bits(values[name], width)} {code}\n")
                previous[name] = values[name]
    return {"bins": 10, "cycles": time_ps // PERIOD_PS,
            "trace_duration_ns": time_ps / 1000, "beta_q": BETA,
            "threshold_q": THRESHOLD, "vcd_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write_conv(out: Path) -> dict:
    path = out / "conv9_activity.vcd"
    lfsr = 0x12D
    with path.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("$timescale 1ps $end\n$scope module conv140k_tb $end\n$scope module dut $end\n")
        handle.write("$var wire 1 ! clk $end\n$var wire 9 \" spike_vector_i [8:0] $end\n")
        handle.write("$var wire 32 # current_delta_o [31:0] $end\n")
        handle.write("$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        for index in range(128):
            lfsr = ((lfsr << 1) | (((lfsr >> 8) ^ (lfsr >> 4)) & 1)) & 0x1FF
            value = sum(weight for bit, weight in enumerate(CONV_WEIGHTS) if (lfsr >> bit) & 1)
            stamp = index * PERIOD_PS
            handle.write(f"#{stamp}\n0!\nb{lfsr:09b} \"\nb{bits(value, 32)} #\n")
            handle.write(f"#{stamp + PERIOD_PS//2}\n1!\n")
    return {"samples": 128, "term_count": 9, "sample_period_ns": 5.0,
            "weights_q7_16": CONV_WEIGHTS,
            "vcd_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    root = Path("artifacts/ASIC/primitive_characterization")
    plif_out = root / "ordinary_plif_1_checkpoint_exact"
    conv_out = root / "detail_stem_conv9_checkpoint_exact"
    plif_out.mkdir(parents=True, exist_ok=True); conv_out.mkdir(parents=True, exist_ok=True)
    plif = write_plif(plif_out); conv = write_conv(conv_out)
    common = {"model": "EventSpikeSeg140k", "checkpoint_epoch": 80,
              "source_actor": "detail_stem", "clock_period_ns": 5.0}
    (plif_out / "activity_manifest.json").write_text(json.dumps(common | plif, indent=2) + "\n")
    (conv_out / "activity_manifest.json").write_text(json.dumps(common | conv, indent=2) + "\n")
    print(json.dumps({"plif": plif, "convolution": conv}, indent=2))


if __name__ == "__main__": main()
