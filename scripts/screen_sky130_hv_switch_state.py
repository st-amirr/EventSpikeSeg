"""Bounded SKY130 public 5V switch-model versus 1.8V TG hold screen."""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
from urllib.request import urlopen

from screen_sky130_mos_state_cap import BENCH, HEADER, OUT, RESULTS, ROOT

HV_MODELS = """.include "../pdk/sky130_fd_pr/cells/nfet_g5v0d10v5/sky130_fd_pr__nfet_g5v0d10v5__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_g5v0d10v5/sky130_fd_pr__pfet_g5v0d10v5__tt.corner.spice"
"""
PUBLIC_BASE = "https://raw.githubusercontent.com/google/skywater-pdk-libs-sky130_fd_pr/main/cells"
EXPECTED_MODEL_SHA256 = {
    "sky130_fd_pr__nfet_g5v0d10v5__tt.corner.spice": "c6220fd1b3ed009078cc3bfe66f6fabccddd5b33653c8efd8c9c4b344253cd25",
    "sky130_fd_pr__nfet_g5v0d10v5__tt.pm3.spice": "4552045d9df048f36742b667c0672b5fd4417d5593f462178015f6646a6fef50",
    "sky130_fd_pr__pfet_g5v0d10v5__tt.corner.spice": "52707b93246551402e9467132ce3d9cb4939d810cd910aa9968dbd534e3f7907",
    "sky130_fd_pr__pfet_g5v0d10v5__tt.pm3.spice": "c438f61902b269fea15355003564c83840661945ac5da8c9dd0d910d3223f21b",
}


def ensure_public_models() -> None:
    for filename, expected_hash in EXPECTED_MODEL_SHA256.items():
        kind = filename.split("__")[1]
        directory = OUT / "pdk/sky130_fd_pr/cells" / kind
        path = directory / filename
        if path.exists():
            content = path.read_bytes()
        else:
            with urlopen(f"{PUBLIC_BASE}/{kind}/{filename}", timeout=30) as response:
                content = response.read()
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise RuntimeError(f"public PDK model hash differs from the screened version: {filename}")
        if not path.exists():
            directory.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def deck(bias: float) -> str:
    lines = [HEADER, HV_MODELS, f"Vprogram src 0 {bias}",
             "Von on 0 PWL(0 1.8 10u 1.8 10.001u 0 5.01m 0)",
             "Voff off 0 PWL(0 0 10u 0 10.001u 1.8 5.01m 1.8)"]
    for kind, nfet, pfet, length in (
        ("lv", "nfet_01v8", "pfet_01v8", 0.15),
        ("hv", "nfet_g5v0d10v5", "pfet_g5v0d10v5", 0.5),
    ):
        lines.append(f"Xsw_n_{kind} src on state_{kind} 0 sky130_fd_pr__{nfet} w=1 l={length}")
        lines.append(f"Xsw_p_{kind} src off state_{kind} vdd sky130_fd_pr__{pfet} w=1 l={length}")
        for finger in range(10):
            lines.append(f"Xcap_{kind}_{finger} 0 state_{kind} 0 0 sky130_fd_pr__nfet_01v8 w=10 l=1")
    lines.extend((".control", "tran 1u 5.01m 0 1u"))
    for kind in ("lv", "hv"):
        lines.extend((f"meas tran {kind}_start find v(state_{kind}) at=12u",
                      f"meas tran {kind}_end find v(state_{kind}) at=5m"))
    lines.extend(("quit", ".endc", ".end"))
    return "\n".join(lines) + "\n"


def main() -> int:
    ensure_public_models()
    BENCH.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for bias in (0.6, 1.2):
        tag = f"sky130_hv_switch_state_{str(bias).replace('.', 'p')}v"
        (BENCH / f"{tag}.cir").write_text(deck(bias), encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
               "--volume", f"{ROOT}:/workspace:ro",
               "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
               "--workdir", "/workspace/artifacts/analog_asic/benches",
               "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36",
               "120", "ngspice", "-b", f"{tag}.cir"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        log = proc.stdout + proc.stderr
        (RESULTS / f"{tag}.log").write_text(log, encoding="utf-8")
        values = {name.lower(): float(value) for name, value in re.findall(
            r"^((?:lv|hv)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log, re.I | re.M)}
        cases = {}
        for kind in ("lv", "hv"):
            start, end = values.get(f"{kind}_start"), values.get(f"{kind}_end")
            cases[kind] = {"start_v": start, "end_v": end,
                           "program_error_v": start - bias if start is not None else None,
                           "hold_drift_v": end - start if start is not None and end is not None else None}
        rows.append({"program_v": bias, "simulation_completed": proc.returncode == 0 and len(values) == 4,
                     "exit_code": proc.returncode, "cases": cases,
                     "failure_hint": next((line for line in log.splitlines()
                                           if "error" in line.lower() or "undefined" in line.lower()), None)})
    report = {
        "scope": "SKY130 TT nominal public 5V gate/10.5V drain transistor models, w=1um l=0.5um TG, compared with installed 1.8V w=1um l=0.15um TG on the same 100um2 MOS gate state. Both use 1.8V controls and a physical 10us sample; 5ms hold. Model revisions not proven identical; no extracted area, noise, mismatch, PVT or 140k service.",
        "model_source": "https://github.com/google/skywater-pdk-libs-sky130_fd_pr/tree/main/cells",
        "public_model_file_sha256": EXPECTED_MODEL_SHA256,
        "all_simulations_completed": all(row["simulation_completed"] for row in rows),
        "results": rows,
    }
    (RESULTS / "sky130_hv_switch_state_boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_simulations_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
