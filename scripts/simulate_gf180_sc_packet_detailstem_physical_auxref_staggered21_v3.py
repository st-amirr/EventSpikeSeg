"""Check interpolation of the extracted SC packet map at seven stored voltages."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
CELL = "gf180_sc_packet_detailstem_ch3_v4"
SIM = CELL + "_physical_auxref_staggered21_v3"
source = BASE / "benches" / "gf180_sc_state_packet_auxmetal_v1_beta_noaux_calibrated_packet_map_v1.spice"
bench = BASE / "benches" / (SIM + ".spice")
logpath = BASE / "results" / (SIM + ".log")
report = BASE / "results" / (SIM + ".json")
assert not any(p.exists() for p in (bench, logpath, report))
text = source.read_text().replace("gf180_sc_state_packet_auxmetal_v1", CELL)
header = text[:text.index("Vdd_low_pos")]
header += '.lib /workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice/sm141064.spice res_typical\n.include /workspace/artifacts/analog_asic/layout/gf180_aux_reference_divider_v2/gf180_aux_reference_divider_v2_cap.spice\nVrefrail ref_vdd 0 3.3\nXreference ref_vdd auxref ref_mid 0 gf180_aux_reference_divider_v2\n' 
template = re.search(r"(?ms)^Vdd_low_pos .*?^\.ic [^\n]*", text)[0]


def interpolate(x, anchors):
    for a, b in zip(anchors, anchors[1:]):
        if a[0] <= x <= b[0]:
            f = (x - a[0]) / (b[0] - a[0])
            return a[1] + f * (b[1] - a[1])
    raise ValueError(x)


cases = []
lines = [header]
for i in range(7):
    state = 0.75 + 0.30 * i
    baseline = interpolate(state, [(0.75, .899545), (1.65, 1.697545), (2.55, 2.497545)])
    zero = interpolate(state, [(0.75, .0793), (1.65, .0695), (2.55, .0554)])
    span = interpolate(state, [(0.75, .0242), (1.65, .0245), (2.55, .0242)])
    for sign, target in (("neg", -8.0), ("zero", 0.0), ("pos", 8.0)):
        tag = f"s{i}_{sign}"
        event = baseline + zero + target / 8.0 * span
        block = template.replace("low_pos", tag)
        block = re.sub(r"(?m)^Vauxref_.*\n", "", block)
        block = block.replace(f"auxref_{tag}", "auxref")
        begin=20+len(cases);end=35.125+len(cases)
        block=re.sub(r'(?m)^Vbeta_.*$',f'Vbeta_{tag} beta_{tag} 0 PWL(0 0 {begin-.01}u 0 {begin}u 3.3 {end-.01}u 3.3 {end}u 0 130u 0)',block)
        block = re.sub(r"(?m)^Vdata_.*$", f"Vdata_{tag} data_{tag} 0 {state:.9f}", block)
        block = re.sub(r"(?m)^Vweight_.*$", f"Vweight_{tag} weight_{tag} 0 PWL(0 {baseline:.9f} 99.999u {baseline:.9f} 100u {event:.9f} 116.5u {event:.9f} 116.501u {baseline:.9f} 130u {baseline:.9f})", block)
        block = re.sub(r"(?m)^\.ic .*$", f".ic v(state_{tag})={state:.9f} v(aux_{tag})=1.65 v(pkt_top_{tag})={state:.9f} v(pkt_bottom_{tag})={state:.9f}", block)
        lines.append(block)
        cases.append({"case": tag, "initial_state_v": state, "baseline_v": baseline, "event_source_v": event, "target_packet_mv": target})
lines += [".control", "set numdgt=15", "tran 20n 130u 0 20n uic"]
measurements = [("pre_beta", 19e-6), ("post_beta", 59e-6), ("pre_event", 99e-6), ("post_release", 120e-6)]
for case in cases:
    for name, at in measurements:
        lines.append(f"meas tran {case['case']}_{name} find v(state_{case['case']}) at={at}")
for name,at in [('ref_before',19e-6),('ref_beta_edge',20.001e-6),('ref_after_beta',59e-6),('ref_after_packet',120e-6)]:
    lines.append(f'meas tran {name} find v(auxref) at={at}')
lines += ['meas tran ref_current_avg avg i(Vrefrail) from=10u to=130u']
lines += ["quit", ".endc", ".end", ""]
bench.write_text("\n".join(lines), encoding="utf8")
run = subprocess.run(["docker", "run", "--rm", "--network", "none", "--memory", "2g", "--cpus", "2", "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice47", "180", "ngspice", "-b", "/workspace/" + bench.relative_to(ROOT).as_posix()], capture_output=True, text=True, timeout=190)
log = run.stdout + run.stderr
logpath.write_text(log, encoding="utf8")
values = {k.lower(): float(v) for k, v in re.findall(r"(?mi)^([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", log)}
assert run.returncode == 0 and "ngspice-47 done" in log.lower() and "timestep too small" not in log.lower(), log[-2000:]
for case in cases:
    for name, _ in measurements:
        case[name + "_v"] = values[case["case"] + "_" + name]
    case["measured_packet_mv"] = (case["post_release_v"] - case["pre_event_v"]) * 1000
    case["packet_error_mv"] = case["measured_packet_mv"] - case["target_packet_mv"]
    case["handoff_displacement_mv"] = (case["pre_event_v"] - case["post_beta_v"]) * 1000
for case in cases:
    case["trained_beta"] = 0.8818925023078918
    case["target_pre_event_v"] = 1.65 + case["trained_beta"] * (case["pre_beta_v"] - 1.65)
    case["beta_and_handoff_error_mv"] = (case["pre_event_v"] - case["target_pre_event_v"]) * 1000
result = {"simulation_completed": True, "cell": CELL, "corner": "GF180 typical, 27C", "cases": cases, "max_packet_error_mv": max(abs(c["packet_error_mv"]) for c in cases), "scope": "Seven initial-state voltages and three commanded charge levels for original-float detail_stem channel3 beta on the routed extracted parent, using interpolation of three externally supplied calibration anchors. The donor beta auxiliary reference is frozen at 1.594V. This 130us screen measures integration error against trained beta; it does not qualify physical reference generation, original-float weight precision, noise/PVT, model accuracy or 5ms service.", "sha256": {"bench": hashlib.sha256(bench.read_bytes()).hexdigest(), "source_bench": hashlib.sha256(source.read_bytes()).hexdigest(), "netlist": hashlib.sha256((BASE / "layout" / CELL / (CELL + "_cap.spice")).read_bytes()).hexdigest(), "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
result['physical_reference']={'cell':'gf180_aux_reference_divider_v2','shared_parent_count':len(cases),'measured_voltages_v':{k:values[k] for k in ['ref_before','ref_beta_edge','ref_after_beta','ref_after_packet']},'average_supply_current_a':-values['ref_current_avg'],'reference_netlist_sha256':hashlib.sha256((BASE/'layout/gf180_aux_reference_divider_v2/gf180_aux_reference_divider_v2_cap.spice').read_bytes()).hexdigest()}
result['physical_reference']['native_decap_cell']='gf180_mim_22x22'
result['physical_reference']['beta_edge_spacing_us']=1.0
result['physical_reference']['beta_edge_slew_ns']=10.0
result['scope']='Two separately routed/extracted layouts connected through ideal bench interconnect: one native three-poly-resistor divider and22x22um native MIM decoupling capacitor drive21 SC parents, with1us spacing between beta edges. Physical inter-macro routing, reference noise/PVT/mismatch, weight/VCM references, all trained beta channels, model/service and chip remain unqualified.'
report.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"report": str(report), "case_count": len(cases), "max_packet_error_mv": result["max_packet_error_mv"]}, indent=2))



