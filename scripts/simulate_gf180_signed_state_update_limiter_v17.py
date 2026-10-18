"""Transient-screen the routed signed-update parent with its extracted rail TGs."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
CELL = "gf180_signed_state_update_limiter_v10"
SIM = "gf180_signed_state_update_limiter_v17"
layout = BASE / "layout" / CELL
netlist = layout / f"{CELL}_cap.spice"
bench = BASE / "benches" / f"{SIM}.spice"
log_path = BASE / "results" / f"{SIM}.log"
report_path = BASE / "results" / f"{SIM}.json"
assert not any(path.exists() for path in (bench, log_path, report_path))
qualification = json.loads((layout / "qualification.json").read_text())
ports = qualification["ports"]
models = BASE / "pdk/gf180_primitive_source/models/ngspice"
lines = [
    "GF180 extracted signed-update parent and routed phase-gated rail limiter",
    ".include /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/design.spice",
    ".lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice typical",
    ".lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice mimcap_typical",
    ".temp 27",
    ".options method=gear reltol=1e-6 abstol=1e-18 vntol=1e-10 gmin=1e-18",
    ".global VSUBS",
    "Vsub VSUBS 0 0",
    f'.include /workspace/{netlist.relative_to(ROOT).as_posix()}',
    "Vdd vdd 0 3.3",
    "Vss vss 0 0",
    "Vbias bias 0 0.75",
    "Vreset reset 0 1.2",
    "Vrampbias rampbias 0 2.6",
    "Vrampcas rampcas 0 2.2",
    "Vpprogram pprogram 0 2.6",
    "Vnprogram nprogram 0 0.455",
    "Vpcas pcas 0 2.2",
    "Vncas ncas 0 1.1",
    "Vwritecommand writecommand 0 PWL(0 3.3 1009.99u 3.3 1010u 0 5m 0)",
    "Xb_write writecommand writeb vdd 0 gf180_phase_inverter_fullroute",
    "Xc_write writeb write vdd 0 gf180_phase_inverter_fullroute",
    "Varm arm 0 0",
    "Varmb armb 0 3.3",
    "Vmag mag 0 0",
    "Vsign sign 0 0",
    "Vdata data 0 0.75",
    "Vauxreset auxreset 0 PWL(0 3.3 2u 3.3 2.01u 0 5m 0)",
    "Vbeta beta 0 0",
    "Vauxref auxref 0 1.65",
    "Vvcm vcm 0 1.65",
]
cases = [("lo", 0.75, -1, 0.7496)]
for tag, initial, sign, rail in cases:
    lines += [
        f"Vrail_{tag} rail_{tag} 0 {rail}",
        f"Vlim_{tag} lim_src_{tag} 0 PWL(0 0 1029u 0 1030u 3.3 1039u 3.3 1040u 0 5m 0)",
        f"Vlimb_{tag} limb_src_{tag} 0 PWL(0 3.3 1029u 3.3 1030u 0 1039u 0 1040u 3.3 5m 3.3)",
        f"Rlim_{tag} lim_src_{tag} lim_{tag} 1k",
        f"Rlimb_{tag} limb_src_{tag} limb_{tag} 1k",
        f"Ipacket_{tag} state_{tag} 0 PWL(0 0 1019.99u 0 1020u {0.44 if sign < 0 else 0}n 1021u {0.44 if sign < 0 else 0}n 1021.01u 0 5m 0)" if sign < 0 else
        f"Ipacket_{tag} 0 state_{tag} PWL(0 0 1019.99u 0 1020u 0.44n 1021u 0.44n 1021.01u 0 5m 0)",
        f".ic v(state_{tag})={initial} v(lim_{tag})=0 v(limb_{tag})=3.3",
    ]
    mapping = {
        "MAG_DATA": "mag", "WRITE": "write", "WRITEB": "writeb", "ARM": "arm", "ARMB": "armb",
        "BIAS": "bias", "VRESET": "reset", "RAMP_BIAS": "rampbias", "RAMP_CAS": "rampcas",
        "VDD": "vdd", "VSS": "vss", "SIGN": "sign", "STATE": f"state_{tag}",
        "PPROGRAM": "pprogram", "NPROGRAM": "nprogram", "PCAS": "pcas", "NCAS": "ncas",
        "PULSE": "pulse", "PULSEB": "pulseb", "POS": "pos", "NEG": "neg", "DATA": "data",
        "AUX": "aux", "AUXRESET": "auxreset", "BETA": "beta", "AUXREF": "auxref", "VCM": "vcm",
        "VRAIL_LO": f"rail_{tag}" if tag == "lo" else "vcm",
        "VRAIL_HI": f"rail_{tag}" if tag == "hi" else "vcm",
        "LIMIT_LO": f"lim_{tag}" if tag == "lo" else "vss",
        "LIMIT_LOB": f"limb_{tag}" if tag == "lo" else "vdd",
        "LIMIT_HI": f"lim_{tag}" if tag == "hi" else "vss",
        "LIMIT_HIB": f"limb_{tag}" if tag == "hi" else "vdd",
    }
    assert set(mapping) == set(ports)
    lines.append(f"Xdut_{tag} " + " ".join(mapping[port] for port in ports) + f" {CELL}")
lines += [".control", "set numdgt=15", "tran 0.2u 5m 0 0.2u uic"]
for tag, initial, _, _ in cases:
    lines += [
        f"meas tran {tag}_pre_packet find v(state_{tag}) at=1019u",
        f"meas tran {tag}_post_packet find v(state_{tag}) at=1022u",
        f"meas tran {tag}_post_limiter find v(state_{tag}) at=1042u",
        f"meas tran {tag}_5ms find v(state_{tag}) at=5m",
    ]
lines += ["quit", ".endc", ".end", ""]
bench.write_text("\n".join(lines), encoding="utf8")
run = subprocess.run(
    ["docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2", "--volume",
     f"{ROOT}:/workspace", "--workdir", "/workspace", "--entrypoint", "timeout",
     "eventspikeseg:analog-ngspice47", "570", "ngspice", "-b", "/workspace/" + bench.relative_to(ROOT).as_posix()],
    capture_output=True, text=True, timeout=580,
)
log = run.stdout + run.stderr
log_path.write_text(log, encoding="utf8")
values = {key.lower(): float(value) for key, value in re.findall(
    r"(?mi)^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", log)}
keys = [f"{tag}_{name}" for tag, *_ in cases for name in ("pre_packet", "post_packet", "post_limiter", "5ms")]
assert run.returncode == 0 and "ngspice-47 done" in log.lower() and all(key in values for key in keys), log[-3000:]
rows = []
for tag, initial, _, rail in cases:
    row = {name: values[f"{tag}_{name}"] for name in ("pre_packet", "post_packet", "post_limiter", "5ms")}
    row["initial_v"] = initial
    row["rail_reference_v"] = rail
    row["packet_delta_mv"] = (row["post_packet"] - row["pre_packet"]) * 1e3
    row["limiter_correction_mv"] = (row["post_limiter"] - row["post_packet"]) * 1e3
    row["rail_error_after_5ms_uv"] = (row["5ms"] - rail) * 1e6
    rows.append({"case": tag, **row})
report = {
    "simulation_completed": True,
    "cell": CELL,
    "corner": "GF180 typical, 27C",
    "cases": rows,
    "scope": "5ms transient of the physically routed extracted composite, with ideal external packet current, rail values, and limiter phase controls. Tests the combined extracted parent/limiter parasitics and routing. Does not test a physical range comparator, calibrated float weight mapping, PVT/noise/mismatch, full PLIF recurrence, or model accuracy.",
    "source_sha256": {
        netlist.relative_to(ROOT).as_posix(): hashlib.sha256(netlist.read_bytes()).hexdigest(),
        bench.relative_to(ROOT).as_posix(): hashlib.sha256(bench.read_bytes()).hexdigest(),
    },
}
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
print(json.dumps(report, indent=2))
