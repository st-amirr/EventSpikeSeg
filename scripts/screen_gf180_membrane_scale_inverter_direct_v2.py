"""Isolate the extracted GF180 inverse amplifier polarity/gain for scale control."""
import hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
CELL = BASE / "layout/gf180_inverse_amplifier_rf126_guarded"
AMP = CELL / "gf180_inverse_amplifier_rf126_guarded_cap.spice"
MODEL = BASE / "pdk/gf180_primitive_source/models/ngspice"
NAME = "gf180_membrane_scale_inverter_direct_v2"
DECK = BASE / "benches" / f"{NAME}.spice"
LOG = BASE / "results" / f"{NAME}.log"
OUT = BASE / "results" / f"{NAME}.json"
CONTROL = (0.75, 1.6973421760170977, 2.55)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not any(path.exists() for path in (DECK, LOG, OUT))
    qualification = json.loads((CELL / "qualification.json").read_text())
    assert qualification["magic_drc_count"] == 0
    assert qualification["lvs_unique"]
    assert qualification["gds_roundtrip_drc_count"] == 0
    assert qualification["gds_roundtrip_lvs_unique"]
    model_prefix = "/workspace/" + MODEL.relative_to(ROOT).as_posix()
    amp_path = "/workspace/" + AMP.relative_to(ROOT).as_posix()
    times = (5, 15, 25)
    lines = [
        f".include {model_prefix}/design.spice",
        f".lib {model_prefix}/sm141064.spice typical",
        f".lib {model_prefix}/sm141064.spice mimcap_typical",
        f".lib {model_prefix}/sm141064.spice res_typical",
        f".include {amp_path}", ".temp 27",
        ".options method=gear reltol=1e-6 abstol=1e-19 vntol=1e-10 gmin=1e-18",
        ".param sw_stat_global=0 sw_stat_mismatch=0", "Vdd vdd 0 3.3",
        "Ireference bias 0 1u",
        "Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u",
        "Vbuf buf 0 PWL(0 0.75 9.99u 0.75 10u 1.697342176 19.99u 1.697342176 20u 2.55 35u 2.55)",
        "Vref ref 0 1.6491",
        "Xamp buf ref sum gate vdd 0 bias cmp r1 r2 r3 gf180_inverse_amplifier_rf126_guarded",
        "Vdrain drain 0 1.65", "Vmeter scale_current drain 0",
        "Mscale scale_current gate vdd vdd pfet_03v3 w=0.42u l=10u",
        ".control", "set numdgt=15", "tran 2n 30u 0 2n uic",
    ]
    for label, time in zip(("min", "median", "max"), times):
        lines.extend([
            f"meas tran scale_gate_{label} find v(gate) at={time}u",
            f"meas tran scale_current_{label} find i(Vmeter) at={time}u",
        ])
    lines.extend(["quit", ".endc", ".end", ""])
    DECK.write_text("\n".join(lines), encoding="utf-8")
    command = [
        "docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2",
        "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace",
        "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "120", "ngspice", "-b",
        "/workspace/" + DECK.relative_to(ROOT).as_posix(),
    ]
    run = subprocess.run(command, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    LOG.write_text(log, encoding="utf-8")
    values = {key: float(value) for key, value in re.findall(
        r"(?m)^(scale_(?:gate|current)_(?:min|median|max))\s*=\s*([-+0-9.eE]+)", log
    )}
    complete = run.returncode == 0 and len(values) == 6
    currents = [values.get(f"scale_current_{label}") for label in ("min", "median", "max")]
    ratios = None
    if complete and all(value is not None and value > 0 for value in currents):
        ratios = {"min_to_median": currents[1] / currents[0],
                  "median_to_max": currents[2] / currents[1],
                  "min_to_max": currents[2] / currents[0]}
    result = {
        "simulation_completed": complete,
        "returncode": run.returncode,
        "simulator": "ngspice 47; GF180 typical 27C; extracted routed inverse OTA and resistor network with native parasitics",
        "control_voltage_v": list(CONTROL),
        "measurements": values,
        "scale_current_ratios": ratios,
        "scope": "Direct ideal scale voltage drives BUF solely to isolate extracted amplifier polarity, gain, and settling. Divider, held coefficient, current multiplier, membrane update, PVT/noise/mismatch, layout, original-float inference, and 5ms service are not tested.",
        "sha256": {path.relative_to(ROOT).as_posix(): sha(path) for path in (DECK, LOG, AMP, CELL / "qualification.json")},
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), "completed": complete,
                      "measurements": values, "scale_current_ratios": ratios}, indent=2))
    if not complete:
        raise RuntimeError(log[-3000:])


if __name__ == "__main__":
    main()
