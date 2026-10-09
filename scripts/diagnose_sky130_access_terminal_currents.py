"""Separate held/source/body/gate DC currents using extracted TG geometries."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
PEX = BASE / "layout/sky130_body_tied_transmission_gate/sky130_body_tied_transmission_gate_pex.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"


def main() -> None:
    geometry = {}
    for line in PEX.read_text(encoding="ascii").splitlines():
        if line.startswith(("X0 ", "X1 ")):
            tokens = line.split()
            geometry["n" if "nfet" in tokens[5] else "p"] = " ".join(tokens[5:])
    if set(geometry) != {"n", "p"}:
        raise RuntimeError("extracted device geometry missing")
    lines = ["* Extracted TG device geometries; DC terminal-current accounting",
             ".options scale=1u gmin=1e-18 reltol=1e-6 abstol=1e-18 vntol=1e-11",
             f'.lib "{LIB}" ff', ".temp 85"]
    cases = []
    aliases = []
    for mode in ("statebody", "fixedbody"):
        for overdrive in (0.0, 0.3):
            for state_v in (0.6, 0.899, 0.901, 1.2):
                label = f"c{len(cases)}"
                cases.append({"label": label, "body_mode": mode,
                              "off_overdrive_v": overdrive, "state_v": state_v})
                for device in ("n", "p"):
                    prefix = f"{label}_{device}"
                    body_v = state_v if mode == "statebody" else (0.0 if device == "n" else 1.8)
                    gate_v = -overdrive if device == "n" else 1.8 + overdrive
                    for terminal, voltage in (("d", state_v), ("s", 0.9),
                                              ("b", body_v), ("g", gate_v)):
                        lines.append(f"V{prefix}_{terminal} {prefix}_{terminal} 0 {voltage:.12g}")
                        aliases.append(f"{prefix}_{terminal}")
                    lines.append(f"X{prefix} {prefix}_d {prefix}_g {prefix}_s {prefix}_b {geometry[device]}")
    lines += [".control", "set numdgt=15", "op"]
    for alias in aliases:
        lines += [f"let {alias}_i = i(v{alias})", f"print {alias}_i"]
    lines += ["quit", ".endc", ".end", ""]
    stem = "sky130_access_terminal_currents_ff85_ngspice47_gmin1e-18"
    deck = BASE / f"benches/{stem}.cir"
    deck.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "60", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    log_path = BASE / f"results/{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    values = {k: float(v) for k, v in re.findall(r"(?m)^(c\d+_[np]_[dsbg]_i)\s*=\s*([-+0-9.eE]+)", log)}
    complete = proc.returncode == 0 and "ngspice-47 done" in log and len(values) == len(aliases)
    if complete:
        for case in cases:
            case["devices"] = {}
            for device in ("n", "p"):
                currents = {terminal: values[f"{case['label']}_{device}_{terminal}_i"]
                            for terminal in ("d", "s", "b", "g")}
                currents["terminal_kcl_residual_a"] = sum(currents.values())
                case["devices"][device] = currents
    report = {"test": "sky130_access_dc_terminal_current_diagnosis",
              "simulation_completed": complete, "return_code": proc.returncode,
              "corner": "FF", "temperature_c": 85, "gmin_siemens": 1e-18,
              "current_sign": "Positive voltage-source branch current flows from terminal to ground; negative supplies current to device",
              "cases": cases if complete else [],
              "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (PEX, deck, log_path)},
              "limitations": "DC voltage-clamped terminals with extracted transistor dimensions, not transient retention or silicon leakage. Omits capacitive PEX and drawn-well diode proxies to isolate MOS terminal paths. State-body metal routing remains a probe assumption. Does not qualify gate bias reliability, noise, physical write/read, area, service or full-float fidelity."}
    out = BASE / f"results/{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "completed": complete, "cases": report["cases"]}, indent=2))
    if not complete:
        raise RuntimeError(log[-1500:])


if __name__ == "__main__":
    main()
