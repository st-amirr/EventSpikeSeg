"""Test the scale current transfer with a native-resistor low-gain OTA."""
import hashlib, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
CELL = BASE / "layout/gf180_inverse_amplifier_rf126_guarded"
AMP = CELL / "gf180_inverse_amplifier_rf126_guarded_cap.spice"
MODEL = BASE / "pdk/gf180_primitive_source/models/ngspice"
NAME = "gf180_membrane_scale_lowgain_v3"
DECK = BASE / "benches" / f"{NAME}.spice"
LOG = BASE / "results" / f"{NAME}.log"
OUT = BASE / "results" / f"{NAME}.json"
VMID = 1.6973421760170977
GAIN = 25.8 / 123.0
VREF = (2.95 + GAIN * 0.75) / (1 + GAIN)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not any(path.exists() for path in (DECK, LOG, OUT))
    qualification = json.loads((CELL / "qualification.json").read_text())
    assert qualification["magic_drc_count"] == 0 and qualification["lvs_unique"]
    assert qualification["gds_roundtrip_drc_count"] == 0 and qualification["gds_roundtrip_lvs_unique"]
    prefix = "/workspace/" + MODEL.relative_to(ROOT).as_posix()
    amp = "/workspace/" + AMP.relative_to(ROOT).as_posix()
    lines = [
        f".include {prefix}/design.spice", f".lib {prefix}/sm141064.spice typical",
        f".lib {prefix}/sm141064.spice mimcap_typical", f".lib {prefix}/sm141064.spice res_typical",
        f".include {amp}", ".temp 27",
        ".options method=gear reltol=1e-6 abstol=1e-19 vntol=1e-10 gmin=1e-18",
        ".param sw_stat_global=0 sw_stat_mismatch=0", "Vdd vdd 0 3.3",
        "Ireference bias 0 1u",
        "Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u",
        f"Vbuf buf 0 PWL(0 0.75 9.99u 0.75 10u {VMID:.12g} 19.99u {VMID:.12g} 20u 2.55 35u 2.55)",
        f"Vref ref 0 {VREF:.12g}",
        "Xota ref sum gate vdd 0 bias cmp gf180_shared_ota_core_pmos_input_fullroute",
        "Xcomp cmp gate cap_mim_2f0_m4m5_noshield c_length=7u c_width=7u",
        "Xrin buf sum 0 ppolyf_u_1k r_width=1u r_length=123u",
        f"Xrf gate sum 0 ppolyf_u_1k r_width=1u r_length={25.8}u",
        "Vdrain drain 0 1.65", "Vmeter scale_current drain 0",
        "Mscale scale_current gate vdd vdd pfet_03v3 w=0.42u l=10u",
        ".control", "set numdgt=15", "tran 2n 30u 0 2n uic",
    ]
    for label, at in (("min", 5), ("median", 15), ("max", 25)):
        lines.extend([f"meas tran scale_gate_{label} find v(gate) at={at}u",
                      f"meas tran scale_current_{label} find i(Vmeter) at={at}u"])
    lines += ["quit", ".endc", ".end", ""]
    DECK.write_text("\n".join(lines), encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice47", "120", "ngspice", "-b",
           "/workspace/" + DECK.relative_to(ROOT).as_posix()]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    LOG.write_text(log, encoding="utf-8")
    values = {key: float(value) for key, value in re.findall(
        r"(?m)^(scale_(?:gate|current)_(?:min|median|max))\s*=\s*([-+0-9.eE]+)", log)}
    complete = run.returncode == 0 and len(values) == 6
    currents = [values.get(f"scale_current_{x}") for x in ("min", "median", "max")]
    ratios = None
    if complete and all(x is not None and x > 0 for x in currents):
        ratios = {"min_to_median": currents[1] / currents[0],
                  "median_to_max": currents[2] / currents[1], "min_to_max": currents[2] / currents[0]}
    target = {"min_to_median": 0.00879502804440424 / 4.711989364483728e-05,
              "median_to_max": 0.5725728280144466 / 0.00879502804440424}
    errors = {k: 100 * (ratios[k] / target[k] - 1) for k in target} if ratios else None
    result = {
        "simulation_completed": complete, "returncode": run.returncode,
        "simulator": "ngspice 47; GF180 typical 27C; extracted routed OTA core plus native poly feedback/input resistor models and MIM compensation",
        "target_scale_ratios": target, "measured_current_ratios": ratios, "relative_error_percent": errors,
        "measurements": values,
        "settings": {"control_voltage_v": [0.75, VMID, 2.55], "input_resistor_length_um": 123,
                     "feedback_resistor_length_um": 25.8, "designed_gain_magnitude": GAIN,
                     "reference_v": VREF, "scale_pfet": "pfet_03v3 w=0.42um l=10um"},
        "scope": "The behavioral divider was replaced with a low-gain native-resistor inverting OTA to isolate the achievable current transfer. The scale input is still ideal; resistor network and OTA are not combined as a new routed macro. No held bank coefficient, current multiplier, membrane update, PVT/mismatch/noise, original-float inference, or 5ms service is qualified.",
        "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in (DECK, LOG, AMP, CELL / "qualification.json")},
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(), "completed": complete,
                      "measurements": values, "ratios": ratios, "errors": errors}, indent=2))
    if not complete:
        raise RuntimeError(log[-3000:])


if __name__ == "__main__":
    main()
