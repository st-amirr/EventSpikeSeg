"""Archive seven core documents and record physically extracted packet mapping."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "artifacts/analog_asic/tools/yaml_validation"))
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = ROOT / "artifacts/analog_asic"
CELL = "gf180_sc_state_packet_auxmetal_v1"
endpath = BASE / "results" / (CELL + "_beta_noaux_calibrated_packet_map_v1.json")
mappath = BASE / "results" / (CELL + "_state_map21_v1.json")
qpath = BASE / "layout" / CELL / "qualification.json"
end = json.loads(endpath.read_text())
mapping = json.loads(mappath.read_text())
q = json.loads(qpath.read_text())
assert end["simulation_completed"] and mapping["simulation_completed"]
assert q["magic_drc_count"] == 0 and q["lvs_unique"] and q["gds_roundtrip_drc_count"] == 0 and q["gds_roundtrip_lvs_unique"]
assert hashlib.sha256((qpath.parent / (CELL + "_cap.spice")).read_bytes()).hexdigest() == end["sha256"]["netlist"] == mapping["sha256"]["netlist"]
names = ["ACTIVE_TASKS.md", "AGENTS.md", "ARCHITECTURE.md", "DECISIONS.md", "PROGRESS.md", "RESULTS.md", "project_spec.yaml"]
original = {n: (DOCS / n).read_bytes() for n in names}
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
archive = BASE / "documentation_history" / ("project_docs_before_auxmetal_packet_map_" + stamp + ".zip")
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for n, content in original.items():
        z.writestr(n, content)
archive.with_suffix(".json").write_text(json.dumps({"archive": archive.relative_to(ROOT).as_posix(), "documents": {n: hashlib.sha256(b).hexdigest() for n, b in original.items()}}, indent=2) + "\n")

stage = "GF180 physically routed switched-capacitor packet mapping. The auxmetal_v1 parent enlarges the existing linear AUX/AUXREF metal plates, adding 5.52fF within the unchanged 0.04925mm2 bounding box; full Magic DRC, unique LVS and GDS readback pass. Extracted low/high signed packet updates are within 0.065mV of +/-8mV and endpoint 5ms hold drift is at most 0.191mV. A 21-case screen across seven initial voltages (0.75-2.55V), with -8/0/+8mV commands, has maximum packet error 0.330mV. Post-beta-to-packet handoff displacement remains up to 7.50mV; this is not a learned-beta accuracy result. Baseline/weight voltages and phases are externally supplied, with UIC initialization. Next implement physical reference delivery and learned-beta control, test actual original-float packet sequences, then bind shared compute/service and finish full-chip assembly. Accuracy, PVT/noise and 5ms population service remain unqualified."
active = original["ACTIVE_TASKS.md"].decode("utf8")
active, count = re.subn(r"\*\*Current stage:[^\r\n]+", "**Current stage: " + stage + "**", active, count=1)
assert count == 1
item = "2. **Switched-capacitor membrane update parent:** auxmetal_v1 is the latest physical candidate (same 0.04925mm2 footprint; full DRC/LVS/GDS readback). Calibrated extracted endpoints deliver +7.987/-7.935mV low and +7.960/-8.000mV high; 5ms drift <=0.191mV. Seven-state, three-command interpolation screen has <=0.330mV packet error. Handoff displacement remains <=7.50mV. Implement and qualify physical baseline/weight reference generation and per-channel learned beta, then original-float event sequences and shared-service binding. Evidence: `artifacts/analog_asic/layout/gf180_sc_state_packet_auxmetal_v1/qualification.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_beta_noaux_calibrated_packet_map_v1.json`, and `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_state_map21_v1.json`."
active, count = re.subn(r"2\. \*\*Switched-capacitor membrane update parent:[^\r\n]+", item, active, count=1)
assert count == 1
spec = original["project_spec.yaml"].decode("utf8")
spec, count = re.subn(r'^  current_stage: "[^\r\n]*"', "  current_stage: " + json.dumps(stage), spec, count=1, flags=re.M)
assert count == 1
entry = {"stage": "extracted_packet_voltage_mapping", "cell": CELL, "qualification": qpath.relative_to(ROOT).as_posix(), "endpoint_5ms_report": endpath.relative_to(ROOT).as_posix(), "state_map_report": mappath.relative_to(ROOT).as_posix(), "actual_added_aux_cap_ff": 5.52273, "footprint_mm2": .04924815, "max_endpoint_packet_error_mv": max(abs(c["net_update_mv"] - (8 if c["case"].endswith("pos") else -8)) for c in end["cases"]), "max_endpoint_5ms_drift_mv": max(abs(c["postrelease_hold_drift_mv"]) for c in end["cases"]), "state_map_cases": 21, "max_state_map_packet_error_mv": mapping["max_packet_error_mv"], "physical_reference_delivery_qualified": False, "learned_beta_qualified": False, "original_float_accuracy_accepted": False, "full_chip_accepted": False, "next": "physical_baseline_weight_reference_and_learned_beta_then_actual_float_sequences_shared_compute_binding"}
spec += "\n" + yaml.safe_dump({"gf180_sc_packet_auxmetal_mapping_2026_10_13": entry}, sort_keys=False)
yaml.safe_load(spec)
paragraph = "The physically routed auxmetal_v1 switched-capacitor parent adds 5.52fF by enlarging existing M4/M5 plates from 100 to 240um2, with no bounding-box growth (0.04925mm2). DRC/LVS/GDS readback pass. Extracted calibrated low/high packets deliver +7.987/-7.935mV and +7.960/-8.000mV; endpoint hold drift <=0.191mV over 5ms. Seven initial states and -8/0/+8mV commands (21 cases, 130us) yield <=0.330mV packet error under interpolation of external calibration anchors. Handoff displacement improves to <=7.50mV but learned beta is not qualified. Prior MOS-cap screens are diagnostic only; body-at-VCM variants do not establish a standard substrate implementation. Actual linear metal plates are the carried-forward design. External ideal references/phases, UIC startup, original-float precision, PVT/noise, physical producer bindings and full-population 5ms remain open. Evidence: `artifacts/analog_asic/layout/gf180_sc_state_packet_auxmetal_v1/qualification.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_beta_noaux_calibrated_packet_map_v1.json`, `artifacts/analog_asic/results/gf180_sc_state_packet_auxmetal_v1_state_map21_v1.json`."
(DOCS / "ACTIVE_TASKS.md").write_bytes(active.encode("utf8"))
(DOCS / "project_spec.yaml").write_bytes(spec.encode("utf8"))
for n in ("ARCHITECTURE.md", "DECISIONS.md", "PROGRESS.md", "RESULTS.md"):
    content = original[n] + ("\n\n## Physical switched-capacitor voltage mapping - 2026-10-13\n\n" + paragraph + "\n\nDocumentation archive: `" + archive.relative_to(ROOT).as_posix() + "`.\n").encode("utf8")
    (DOCS / n).write_bytes(content)
print(json.dumps({"archive": str(archive), "documents_updated": 6, "yaml_valid": True, "max_packet_error_mv": mapping["max_packet_error_mv"]}, indent=2))
