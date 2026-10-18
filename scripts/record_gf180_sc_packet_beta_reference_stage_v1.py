"""Audit integrated beta/reference evidence and update the existing project docs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
sys.path.insert(0, str(BASE / "tools/yaml_validation"))
import yaml


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = BASE / "results/gf180_sc_packet_beta_reference_stage_v1.json"
    assert not report.exists()
    paths = set()
    layout_names = ["gf180_sc_packet_detailstem_ch3_v4", "gf180_nf_state_update_aux_overlap386p4", "gf180_aux_reference_divider_v2"]
    layouts = []
    for name in layout_names:
        directory = BASE / "layout" / name
        qp = directory / "qualification.json"
        q = json.loads(qp.read_text())
        assert q["magic_drc_count"] == 0 and q["lvs_unique"] and q["gds_roundtrip_drc_count"] == 0 and q["gds_roundtrip_lvs_unique"]
        paths.add(qp)
        for filename, digest in q["sha256"].items():
            p = directory / filename
            assert sha(p) == digest, str(p)
            paths.add(p)
        layouts.append({"cell": name, "bbox_um": q["bbox_um"], "full_DRC_LVS_GDS_readback": True})
    r = BASE / "results"
    idealp = r / "gf180_sc_packet_detailstem_ch3_v4_trained_beta_packet21_v1.json"
    sharedp = r / "gf180_sc_packet_detailstem_ch3_v4_physical_auxref_staggered21_v3.json"
    badp = r / "gf180_sc_packet_detailstem_ch3_v4_physical_auxref_shared21_v1.json"
    ideal, shared, bad = [json.loads(p.read_text()) for p in (idealp, sharedp, badp)]
    paths.update((idealp, sharedp, badp))
    assert all(d["simulation_completed"] for d in (ideal, shared, bad))
    net = BASE / "layout/gf180_sc_packet_detailstem_ch3_v4/gf180_sc_packet_detailstem_ch3_v4_cap.spice"
    assert sha(net) == ideal["sha256"]["netlist"] == shared["sha256"]["netlist"]
    refnet = BASE / "layout/gf180_aux_reference_divider_v2/gf180_aux_reference_divider_v2_cap.spice"
    assert sha(refnet) == shared["physical_reference"]["reference_netlist_sha256"]
    zero = [c for c in ideal["cases"] if c["target_packet_mv"] == 0]
    beta = (zero[-1]["pre_event_v"] - zero[0]["pre_event_v"]) / (zero[-1]["pre_beta_v"] - zero[0]["pre_beta_v"])
    replay_rows = []
    for record in (8, 64):
        matches = list(r.glob(f"gf180_sc_packet_beta_channel_record{record}_seed0_src*.json"))
        assert len(matches) == 1
        p = matches[0];d = json.loads(p.read_text());paths.add(p)
        assert d["simulation_completed"] and d["baseline_reproduced"] and not d["qat_or_quantized_reference_used"]
        for filename, digest in d["sha256"].items():
            path = ROOT / filename
            assert sha(path) == digest, filename
            paths.add(path)
        baseline, control, measured = d["results"]
        replay_rows.append({"record": record, "baseline_iou": baseline["mean_iou"], "measured_iou": measured["mean_iou"], "iou_change": measured["mean_iou"] - baseline["mean_iou"], "changed_pixels_fraction": measured["pixel_change_fraction"], "range_control_changed_pixels_fraction": control["pixel_change_fraction"], "scope": "One channel, ideal input-current contributions and external calibrated reference; no all-channel accuracy claim."})
    summary = {"audit_completed": True, "checkpoint_sha256": "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7", "target": {"actor": "detail_stem", "channel": 3, "beta": .8818925023078918}, "layouts": layouts, "measured_beta_slope": beta, "ideal_reference_21_case_max_candidate_error_mv": max(abs(c["beta_and_handoff_error_mv"] + c["packet_error_mv"]) for c in ideal["cases"]), "physical_shared_reference": shared["physical_reference"], "physical_reference_21_case_max_candidate_error_mv": max(abs(c["beta_and_handoff_error_mv"] + c["packet_error_mv"]) for c in shared["cases"]), "replays": replay_rows, "rejected_or_incomplete": ["Tall 500um2 auxiliary plate shorts STATE to AUXREF only after parent assembly; preserved v2 failed LVS.", "Undecoupled simultaneous21-lane passive reference jumps to2.17563V and gives11.86mV candidate error.", "Two1ns staggered-edge runs abort with timestep errors and have no completed result."], "scope": "Original trained single-channel beta and packet parent, separately extracted physical shared reference/decap, nominal seven-state electrical screen. Reference-to-compute wiring remains ideal bench interconnect. Replay uses the ideal-reference measured zero-packet curve; physical-reference replay, all1856 beta channels, physical VCM/weight producers, loaded5ms cycles, PVT/noise, full-chip bindings/layout and model-wide accuracy remain open.", "original_float_accuracy_accepted": False, "full_5ms_population_service_accepted": False, "full_chip_accepted": False, "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}}
    report.write_text(json.dumps(summary, indent=2) + "\n")
    names = ["ACTIVE_TASKS.md", "AGENTS.md", "ARCHITECTURE.md", "DECISIONS.md", "PROGRESS.md", "RESULTS.md", "project_spec.yaml"]
    original = {n: (ROOT / "docs" / n).read_bytes() for n in names}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = BASE / "documentation_history" / ("project_docs_before_sc_beta_reference_" + stamp + ".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, contents in original.items():
            z.writestr(name, contents)
    stage = "GF180 integrated original-channel beta and physical shared-reference qualification. The detail_stem channel3 v4 SC parent passes DRC/LVS/GDS readback in0.04925mm2; actual386.4um2 auxiliary metal plates give measured beta0.88298 versus trained0.88189. Nominal21cases across0.75-2.55V have <=1.89mV combined beta/packet error with external calibrated reference. Two original-float heldout replays reproduce baseline hashes and change1.60/1.83% pixels with IoU+0.00175/+0.00123 for this channel only. Native three-resistor/MIM-decoupled reference v2 also passes physical checks; one extracted reference drives21 extracted parents with1us stagger and10ns beta edges, <=3.54mV candidate error. Inter-macro wiring remains bench-only. Next physically route reference and compute together, qualify actual weight/VCM producers and learned-beta channel coverage, then shared-service/full-chip integration. Full-model accuracy and5ms population service remain unqualified."
    active = original["ACTIVE_TASKS.md"].decode("utf8")
    active, count = re.subn(r"\*\*Current stage:[^\r\n]+", "**Current stage: " + stage + "**", active, count=1);assert count == 1
    task = "2. **Switched-capacitor membrane update parent:** latest trained-channel candidate is `gf180_sc_packet_detailstem_ch3_v4`, beta0.88298 versus original detail_stem channel3 target0.88189. Actual metal-cap sizing, DRC/LVS/GDS readback, seven-state21-case nominal screen and two heldout one-channel float replays complete. Native shared auxiliary-reference divider v2 with MIM decoupling is physically checked;21-load electrical screen completes with1us stagger/10ns edges and<=3.54mV candidate error. Next route the reference-to-compute physical parent and qualify actual VCM/weight delivery, all-channel beta and loaded5ms recurrence. Evidence/limitations: `artifacts/analog_asic/results/gf180_sc_packet_beta_reference_stage_v1.json`."
    active, count = re.subn(r"2\. \*\*Switched-capacitor membrane update parent:[^\r\n]+", task, active, count=1);assert count == 1
    spec = original["project_spec.yaml"].decode("utf8")
    spec, count = re.subn(r'^  current_stage: "[^\r\n]*"', "  current_stage: " + json.dumps(stage), spec, count=1, flags=re.M);assert count == 1
    spec += "\n" + yaml.safe_dump({"gf180_sc_packet_beta_reference_stage_2026_10_13": {"summary": report.relative_to(ROOT).as_posix(), "measured_beta": beta, "target_beta": .8818925023078918, "physical_reference_candidate_error_mv": summary["physical_reference_21_case_max_candidate_error_mv"], "physical_inter_macro_routing_qualified": False, "all_beta_channels_qualified": False, "original_float_accuracy_accepted": False, "full_chip_accepted": False}}, sort_keys=False)
    yaml.safe_load(spec)
    (ROOT / "docs/ACTIVE_TASKS.md").write_bytes(active.encode("utf8"))
    (ROOT / "docs/project_spec.yaml").write_bytes(spec.encode("utf8"))
    text = "\n\n## Integrated trained beta and shared auxiliary reference - 2026-10-13\n\n" + stage + " Evidence and rejected attempts: `" + report.relative_to(ROOT).as_posix() + "`. Archive: `" + archive.relative_to(ROOT).as_posix() + "`.\n"
    for name in ("ARCHITECTURE.md", "DECISIONS.md", "PROGRESS.md", "RESULTS.md"):
        (ROOT / "docs" / name).write_bytes(original[name] + text.encode("utf8"))
    print(json.dumps({"summary": str(report), "measured_beta": beta, "max_physical_reference_candidate_error_mv": summary["physical_reference_21_case_max_candidate_error_mv"], "yaml_valid": True}, indent=2))


if __name__ == "__main__":
    main()
