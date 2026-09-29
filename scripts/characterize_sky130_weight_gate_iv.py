"""Measure SKY130 MOS gate-bias current curves for a possible analog LUT map."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
VDD = 1.8
STATE = 0.9
STEP = 0.01
W_MAX = 68.37539672851562
DEVICE_WIDTH = 2.0
COMMON = """.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
"""


def run(polarity: str) -> list[tuple[float, float]]:
    source = f"""SKY130 {polarity} current source gate transfer
{COMMON}
Vdd vdd 0 {VDD}
Vgate gate 0 0
Vstate state 0 {STATE}
"""
    if polarity == "positive":
        source += f"Xp state gate vdd vdd sky130_fd_pr__pfet_01v8 w=2 l=2\n"
    else:
        source += f"Xn state gate 0 0 sky130_fd_pr__nfet_01v8 w=2 l=2\n"
    source += f""".control
set wr_singlescale
set wr_vecnames
dc Vgate 0 {VDD} {STEP}
wrdata ../results/sky130_weight_gate_iv_{polarity}.dat v(gate) i(Vstate)
quit
.endc
.end
"""
    name = f"sky130_weight_gate_iv_{polarity}"
    (BENCH / f"{name}.cir").write_text(source, encoding="utf-8")
    cmd = [
        "docker", "run", "--rm", "--memory", "1g", "--cpus", "1",
        "--volume", f"{ROOT}:/workspace:ro",
        "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
        "--workdir", "/workspace/artifacts/analog_asic/benches",
        "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
        "30", "ngspice", "-b", f"{name}.cir",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    (RES / f"{name}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"{name} failed ({proc.returncode}): {proc.stdout}\n{proc.stderr}")
    data = RES / f"sky130_weight_gate_iv_{polarity}.dat"
    rows: list[tuple[float, float]] = []
    for line in data.read_text().splitlines()[1:]:
        try:
            values = [float(v) for v in line.split()]
            if len(values) >= 2 and all(math.isfinite(v) for v in values):
                rows.append((values[-2], values[-1]))
        except ValueError:
            continue
    if len(rows) < 100:
        raise RuntimeError(f"{name}: expected >=100 DC points, got {len(rows)}")
    return rows


def gate_at_fraction(rows: list[tuple[float, float]], fraction: float, polarity: str) -> float:
    currents = [abs(current) for _, current in rows]
    target = max(currents) * fraction
    # Positive PMOS is strongest at low gate; NMOS at high gate.
    ordered = list(reversed(rows)) if polarity == "positive" else rows
    for (va, ia), (vb, ib) in zip(ordered, ordered[1:]):
        ca, cb = abs(ia), abs(ib)
        if min(ca, cb) <= target <= max(ca, cb) and ca != cb:
            return va + (target-ca)*(vb-va)/(cb-ca)
    return ordered[-1][0]


def main() -> int:
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    curves = {p: run(p) for p in ("positive", "negative")}
    summaries = {}
    for polarity, rows in curves.items():
        currents = [abs(i) for _, i in rows]
        summaries[polarity] = {
            "points": len(rows),
            "gate_range_v": [rows[0][0], rows[-1][0]],
            "max_abs_current_a": max(currents),
            "min_abs_current_a": min(currents),
            "iv_curve": [
                {"gate_v": gate, "abs_current_a": abs(current)}
                for gate, current in rows
            ],
            "gate_v_for_weight_fraction": {
                str(w): gate_at_fraction(rows, w/W_MAX, polarity)
                for w in (1.0, 8.0, 32.0, 68.0)
            },
        }
    report = {
        "test": "sky130_tt_mos_weight_gate_iv_characterization",
        "state_v": STATE,
        "device_w_l_um": [2, 2],
        "weight_absmax_from_export": W_MAX,
        "sweep_step_v": STEP,
        "curves": summaries,
        "full_scale_current_ratio_positive_over_negative": (
            summaries["positive"]["max_abs_current_a"] /
            summaries["negative"]["max_abs_current_a"]
        ),
        "p_width_for_equal_full_scale_current_um": (
            DEVICE_WIDTH * summaries["negative"]["max_abs_current_a"] /
            summaries["positive"]["max_abs_current_a"]
        ),
        "scope": "Unpulsed single MOS current source I-V curves; no R-2R DAC, pulse switch, mismatch, or extracted layout.",
    }
    (RES / "sky130_weight_gate_iv_characterization.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
