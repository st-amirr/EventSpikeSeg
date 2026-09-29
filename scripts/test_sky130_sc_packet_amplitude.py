"""Screen packet top-plate swing coding on the smallest tested SKY130 MIM packet."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
RES = OUT / "results"
BENCH = OUT / "benches"
VCM = 0.9
SWINGS = (0.005, 0.01, 0.02, 0.04, 0.08, 0.15, 0.30)

def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--state-sweep-original":
        rows = []
        for state_v in (0.75, 0.9, 1.05):
            for amp in (0.02, 0.30):
                proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), f"{amp:g}", "1", f"{state_v:g}", "--original-init"], capture_output=True, text=True)
                if proc.returncode != 0:
                    print(proc.stdout)
                    print(proc.stderr)
                    return proc.returncode
                child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
                for row in child.get("cases", []):
                    row["initial_membrane_state_v"] = state_v
                rows.extend(child.get("cases", []))
        max_error = max(abs(float(row["initial_state_error_v"])) for row in rows)
        report = {"test": "sky130_tt_original_integrator_physical_init_state_sweep", "simulation_completed": len(rows) == 12,
                  "physical_init_max_abs_state_error_v": max_error, "physical_init_smoke_pass": max_error < 0.01,
                  "cases": rows, "scope": "always-connected original OTA; direct TG init to requested output state; 1um packet; same-phase no-event control"}
        (RES / "sky130_sc_packet_original_init_sweep.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_packet_original_init_sweep.json"), "simulation_completed": report["simulation_completed"], "max_init_error_v": max_error}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 2 and sys.argv[1] == "--bias-fine":
        bias_cases = []
        for bias_v in (0.84, 0.86, 0.88, 0.90):
          for tail_v in (0.65, 0.75):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "0.02", "1", "0.9", "--held", f"{bias_v:g}", f"{tail_v:g}"], capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                return proc.returncode
            child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
            for row in child.get("cases", []):
                row["output_stage_bias_v"] = bias_v
                row["input_tail_bias_v"] = tail_v
            bias_cases.extend(child.get("cases", []))
        report = {"test": "sky130_tt_held_integrator_fine_output_bias_sensitivity", "simulation_completed": len(bias_cases) == 16,
                  "mapping_qualified": False, "cases": bias_cases,
                  "scope": "held-output integrator, physical init target 0.9V, 20mV signed top-plate pulse, same-phase no-event control; fine sweep Vbp 0.84–0.90V and Vbn 0.65/0.75V; schematic TT"}
        (RES / "sky130_sc_output_bias_fine_sweep.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_output_bias_fine_sweep.json"), "simulation_completed": report["simulation_completed"]}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 2 and sys.argv[1] == "--bias-sweep":
        bias_cases = []
        for bias_v in (0.60, 0.75, 0.90):
          for tail_v in (0.55, 0.65, 0.75):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "0.02", "1", "0.9", "--held", f"{bias_v:g}", f"{tail_v:g}"], capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                return proc.returncode
            child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
            for row in child.get("cases", []):
                row["output_stage_bias_v"] = bias_v
                row["input_tail_bias_v"] = tail_v
            bias_cases.extend(child.get("cases", []))
        report = {"test": "sky130_tt_held_integrator_output_and_tail_bias_sensitivity", "simulation_completed": len(bias_cases) == 18,
                  "mapping_qualified": False, "cases": bias_cases,
                  "scope": "held-output integrator, physical init target 0.9V, 20mV signed top-plate pulse, same-phase no-event control; vary PMOS output-stage gate bias only; schematic TT"}
        (RES / "sky130_sc_output_bias_sweep.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_output_bias_sweep.json"), "simulation_completed": report["simulation_completed"]}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 2 and sys.argv[1] == "--state-sweep":
        state_cases = []
        for state_v in (0.75, 0.9, 1.05):
            for amp in (0.02, 0.30):
                proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), f"{amp:g}", "1", f"{state_v:g}", "--held"], capture_output=True, text=True)
                if proc.returncode != 0:
                    print(proc.stdout)
                    print(proc.stderr)
                    return proc.returncode
                child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
                for row in child.get("cases", []):
                    row["initial_membrane_state_v"] = state_v
                state_cases.extend(child.get("cases", []))
        max_init_error = max(abs(float(row["physical_init_state_error_v"])) for row in state_cases)
        report = {"test": "sky130_tt_packet_no_event_offset_subtraction_over_membrane_state", "simulation_completed": len(state_cases) == 12,
                  "mapping_qualified": False, "cases": state_cases,
                  "physical_init_max_abs_state_error_v": max_init_error,
                  "physical_init_smoke_pass": max_init_error < 0.01,
                  "scope": "transistor TG init pulse to requested 0.75/0.9/1.05V output state, then 1um packet; same-phase no-event control; isolated simulator per state/swing; correction is bench subtraction only"}
        (RES / "sky130_sc_packet_state_sweep.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_packet_state_sweep.json"), "simulation_completed": report["simulation_completed"]}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 2 and sys.argv[1] == "--retention-sweep":
        retention_cases = []
        for state_v in (0.75, 0.9, 1.05):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "0.02", "1", f"{state_v:g}", "--held-retention"], capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                return proc.returncode
            child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
            retention_cases.extend(child.get("cases", []))
        max_error = max(abs(float(row["idle_retention_error_v"])) for row in retention_cases)
        report = {"test": "sky130_tt_held_membrane_5ms_idle_retention", "simulation_completed": len(retention_cases) == 6,
                  "mapping_qualified": False, "idle_retention_max_abs_error_v": max_error,
                  "idle_retention_smoke_pass_10mV": max_error < 0.01, "cases": retention_cases,
                  "scope": "physical TG initialization to 0.75/0.90/1.05V; OTA/output-connect, packet-connect and packet switching held off for 5ms; nominal TT schematic; isolated simulator runs; no PVT, mismatch, extracted parasitics or noise"}
        (RES / "sky130_sc_physical_retention_sweep.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_physical_retention_sweep.json"), "simulation_completed": report["simulation_completed"], "max_idle_retention_error_v": max_error}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 2 and sys.argv[1] == "--retention-packet-sweep":
        sequence_cases = []
        for state_v in (0.75, 0.9, 1.05):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "0.30", "1", f"{state_v:g}", "--held-retention-packet"], capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                return proc.returncode
            child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
            sequence_cases.extend(child.get("cases", []))
        report = {"test": "sky130_tt_physical_5ms_idle_then_signed_packet", "simulation_completed": len(sequence_cases) == 6,
                  "mapping_qualified": False, "cases": sequence_cases,
                  "scope": "physical TG initialization; 5ms OTA-disconnected idle hold; then OTA reconnect and signed 0.3V packet; event increment subtracts same-state no-event reconnect control; nominal TT schematic, no PVT/mismatch/extraction/noise"}
        (RES / "sky130_sc_physical_retention_packet_sweep.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_physical_retention_packet_sweep.json"), "simulation_completed": report["simulation_completed"], "max_packet_error_v": max(abs(float(row["state_change_v"])) for row in sequence_cases)}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 2 and sys.argv[1] == "--small-caps":
        geometry_cases = []
        for cap_um in (0.25, 0.5, 0.75, 1.0, 3.0, 10.0):
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "0.30", f"{cap_um:g}"], capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                return proc.returncode
            child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
            geometry_cases.extend(child.get("cases", []))
        responses = {}
        for polarity in ("positive", "negative"):
            selected = [row for row in geometry_cases if row["polarity"] == polarity]
            ordered = [abs(float(row["state_change_v"])) for row in selected]
            responses[polarity] = {"absolute_response_monotonic_with_cap_area": all(a <= b for a,b in zip(ordered, ordered[1:])),
                                   "cap_size_um_and_corrected_response_v": [[float(row["packet_size_um"]), float(row["state_change_v"])] for row in selected]}
        report = {"test": "sky130_tt_mim_packet_geometry_sensitivity_with_no_event_baseline", "simulation_completed": len(geometry_cases) == 12,
                  "mapping_qualified": False, "cases": geometry_cases, "response_by_polarity": responses,
                  "geometry_legality": "unknown; the local checkout lacks physical MIM design rules/PCell implementation; model-only dimensions do not prove manufacturability",
                  "scope": "one 0.3V top-plate pulse swing per isolated ngspice process while connected to the virtual-summing node; both signs, .25/.5/.75/1/3/10um square PDK MIM model dimensions; each circuit has a matched same-phase no-event control; nominal TT schematic diagnostic only"}
        (RES / "sky130_sc_small_cap_geometry.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_small_cap_geometry.json"), "simulation_completed": report["simulation_completed"], "response_by_polarity": responses}, indent=2))
        return 0 if report["simulation_completed"] else 2
    if len(sys.argv) == 1:
        isolated_cases = []
        for amp in SWINGS:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), f"{amp:g}"], capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
                return proc.returncode
            child = json.loads((RES / "sky130_sc_packet_amplitude.json").read_text(encoding="utf-8"))
            isolated_cases.extend(child.get("cases", []))
        monotonic = {}
        for polarity in ("positive", "negative"):
            series = [abs(float(row["state_change_v"])) for row in isolated_cases if row["polarity"] == polarity]
            monotonic[polarity] = all(a <= b for a, b in zip(series, series[1:]))
        paired = []
        for amp in SWINGS:
            pos = next(row for row in isolated_cases if row["polarity"] == "positive" and math.isclose(abs(float(row["packet_step_v"])), amp, rel_tol=1e-9))
            neg = next(row for row in isolated_cases if row["polarity"] == "negative" and math.isclose(abs(float(row["packet_step_v"])), amp, rel_tol=1e-9))
            gp, gn = abs(float(pos["state_change_v"])), abs(float(neg["state_change_v"]))
            paired.append({"input_swing_mv": amp*1000, "positive_increment_abs_v": gp, "negative_increment_abs_v": gn,
                           "bipolar_magnitude_mismatch_fraction": abs(gp-gn)/((gp+gn)/2) if gp+gn else None})
        report = {"test": "sky130_tt_1um_packet_top_plate_swing_isolated_runs", "simulation_completed": len(isolated_cases) == 14,
                  "mapping_qualified": False, "cases": isolated_cases,
                  "absolute_response_monotonic_by_sign": monotonic,
                  "bipolar_pairing": paired,
                  "scope": "each amplitude and polarity pair is run in a separate ngspice process; packet top-plate pulse changes while connected to the virtual-summing node; response is measured from the pre-packet sample within the same run; TT schematic only, no mismatch, PVT, extraction or event-sequence qualification"}
        (RES / "sky130_sc_packet_amplitude.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        print(json.dumps({"report": str(RES / "sky130_sc_packet_amplitude.json"), "simulation_completed": report["simulation_completed"], "monotonic": monotonic}, indent=2))
        return 0 if report["simulation_completed"] else 2
    active_swings = (float(sys.argv[1]),)
    cap_um = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    membrane_state_v = float(sys.argv[3]) if len(sys.argv) > 3 else VCM
    use_retention = len(sys.argv) > 4 and sys.argv[4] == "--held-retention"
    use_retention_packet = len(sys.argv) > 4 and sys.argv[4] == "--held-retention-packet"
    use_held = len(sys.argv) > 4 and sys.argv[4] == "--held" or use_retention or use_retention_packet
    use_original_init = len(sys.argv) > 4 and sys.argv[4] == "--original-init"
    use_physical_init = use_held or use_original_init
    init_sample_s = 2.9e-6 if use_held else 0.45e-6
    pre_sample_s = 4.999e-3 if use_retention_packet else (3.0e-6 if use_retention else (3.4e-6 if use_held else 0.9e-6))
    post_sample_s = 5.0035e-3 if use_retention_packet else (5.003e-3 if use_retention else (6.5e-6 if use_held else 3.5e-6))
    sim_stop_s = "5.005m" if use_retention_packet else ("5.005m" if use_retention else ("8u" if use_held else "4u"))
    tran_step = "100n" if use_retention or use_retention_packet else "5n"
    vbiasp_v = float(sys.argv[5]) if len(sys.argv) > 5 else 0.75
    vbiasn_v = float(sys.argv[6]) if len(sys.argv) > 6 else 0.65
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    lines = ["SKY130 TT 1um MIM packet precharge-amplitude screen", """
.option scale=1u
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_ms_plif.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
""", "Vdd vdd 0 1.8", "Vcm vcm 0 0.9", "Vbp vbiasp 0 0.75"]
    vectors: list[str] = []
    cases: list[dict[str, object]] = []
    for amp in active_swings:
        for polarity in ("positive", "negative"):
            name = f"a{int(amp*1000):03d}_{polarity[0]}"
            packet_v = VCM + amp if polarity == "positive" else VCM - amp
            if use_physical_init:
                init_bias = [f"Vbn_{name} vbiasn_{name} 0 {vbiasn_v:g}",
                             f"Vbp_{name} vbiasp_{name} 0 {vbiasp_v:g}",
                             f"Vinitlvl_{name} initlvl_{name} 0 {membrane_state_v:g}",
                             f"Vinit_{name} init_{name} 0 PWL(0 1.8 2.499u 1.8 2.5u 0 8u 0)" if use_held else f"Vinit_{name} init_{name} 0 PWL(0 1.8 0.249u 1.8 0.25u 0 4u 0)",
                             f"Vinitb_{name} initb_{name} 0 PWL(0 0 2.499u 0 2.5u 1.8 8u 1.8)" if use_held else f"Vinitb_{name} initb_{name} 0 PWL(0 0 0.249u 0 0.25u 1.8 4u 1.8)",
                             f".ic v(out_{name})={membrane_state_v:g} v(sum_{name})={VCM}"]
                init_node = f"initlvl_{name}"
                instance_type = "sky130_sc_charge_integrator_held" if use_held else "sky130_sc_charge_integrator"
            else:
                init_bias = [f"Vbn_{name} vbiasn_{name} 0 0.65", f"Vbp_{name} vbiasp_{name} 0 0.75",
                             f"Vinitlvl_{name} initlvl_{name} 0 {VCM}", f"Vinit_{name} init_{name} 0 0",
                             f"Vinitb_{name} initb_{name} 0 1.8", f".ic v(out_{name})={membrane_state_v-VCM} v(sum_{name})={VCM}"]
                init_node = "vcm"
                instance_type = "sky130_sc_charge_integrator"
            amp_phase = ("PWL(0 0 4.999m 0 5m 1.8 5.0025m 1.8 5.00251m 0 5.005m 0)", "PWL(0 1.8 4.999m 1.8 5m 0 5.0025m 0 5.00251m 1.8 5.005m 1.8)") if use_retention_packet else (("PWL(0 0 8u 0 8.001u 0 5.005m 0)", "PWL(0 1.8 8u 1.8 8.001u 1.8 5.005m 1.8)") if use_retention else (("PWL(0 0 2.999u 0 3u 1.8 4.999u 1.8 5u 0 8u 0)", "PWL(0 1.8 2.999u 1.8 3u 0 4.999u 0 5u 1.8 8u 1.8)") if use_held else ("PWL(0 0 0.499u 0 0.5u 1.8 2.499u 1.8 2.5u 0 4u 0)", "PWL(0 1.8 0.499u 1.8 0.5u 0 2.499u 0 2.5u 1.8 4u 1.8)")))
            lines += [
                *init_bias,
                f"Vreset_{name} reset_{name} 0 0", f"Vresetb_{name} resetb_{name} 0 1.8",
                f"Vpacket_reset_{name} packet_reset_{name} 0 0", f"Vpacket_resetb_{name} packet_resetb_{name} 0 1.8",
                f"Vconn_{name} conn_{name} 0 PWL(0 0 4.999m 0 5m 1.8 5.0025m 1.8 5.00251m 0 5.005m 0)" if use_retention_packet else (f"Vconn_{name} conn_{name} 0 PWL(0 0 8u 0 8.001u 0 5.005m 0)" if use_retention else (f"Vconn_{name} conn_{name} 0 PWL(0 0 2.999u 0 3u 1.8 4.999u 1.8 5u 0 8u 0)" if use_held else f"Vconn_{name} conn_{name} 0 PWL(0 0 0.499u 0 0.5u 1.8 2.499u 1.8 2.5u 0 4u 0)")),
                f"Vconnb_{name} connb_{name} 0 PWL(0 1.8 4.999m 1.8 5m 0 5.0025m 0 5.00251m 1.8 5.005m 1.8)" if use_retention_packet else (f"Vconnb_{name} connb_{name} 0 PWL(0 1.8 8u 1.8 8.001u 1.8 5.005m 1.8)" if use_retention else (f"Vconnb_{name} connb_{name} 0 PWL(0 1.8 2.999u 1.8 3u 0 4.999u 0 5u 1.8 8u 1.8)" if use_held else f"Vconnb_{name} connb_{name} 0 PWL(0 1.8 0.499u 1.8 0.5u 0 2.499u 0 2.5u 1.8 4u 1.8)")),
                f"Vamp_{name} amp_{name} 0 {amp_phase[0]}",
                f"Vampb_{name} ampb_{name} 0 {amp_phase[1]}",
                f"Vpkt_{name} ptop_{name} 0 PWL(0 {VCM} 5.0004m {VCM} 5.0005m {packet_v:g} 5.0025m {packet_v:g} 5.0026m {VCM} 5.007m {VCM})" if use_retention_packet else (f"Vpkt_{name} ptop_{name} 0 {VCM}" if use_retention else (f"Vpkt_{name} ptop_{name} 0 PWL(0 {VCM} 3.499u {VCM} 3.5u {packet_v:g} 4.999u {packet_v:g} 5u {VCM} 8u {VCM})" if use_held else f"Vpkt_{name} ptop_{name} 0 PWL(0 {VCM} 0.999u {VCM} 1u {packet_v:g} 2.499u {packet_v:g} 2.5u {VCM} 4u {VCM})")),
                f"Xcell_{name} out_{name} sum_{name} ptop_{name} pbot_{name} reset_{name} resetb_{name} packet_reset_{name} packet_resetb_{name} {init_node} init_{name} initb_{name} conn_{name} connb_{name} " + (f"amp_{name} ampb_{name} " if use_held else "") + f"vbiasn_{name} vbiasp_{name} vdd 0 vcm {instance_type} cmem_um=100 cpacket_um={cap_um:g}",
            ]
            vectors += [f"v(out_{name})", f"v(sum_{name})"]
            cases.append({"name": name, "packet_step_v": packet_v - VCM, "packet_size_um": cap_um, "polarity": polarity})
    # A same-phase no-event cell lets us subtract startup drift and switch feedthrough.
    if use_physical_init:
        base_lines = [f"Vbn_base vbiasn_base 0 {vbiasn_v:g}",
                      f"Vbp_base vbiasp_base 0 {vbiasp_v:g}",
                      f"Vinitlvl_base initlvl_base 0 {membrane_state_v:g}",
                      "Vinit_base init_base 0 PWL(0 1.8 2.499u 1.8 2.5u 0 8u 0)" if use_held else "Vinit_base init_base 0 PWL(0 1.8 0.249u 1.8 0.25u 0 4u 0)",
                      "Vinitb_base initb_base 0 PWL(0 0 2.499u 0 2.5u 1.8 8u 1.8)" if use_held else "Vinitb_base initb_base 0 PWL(0 0 0.249u 0 0.25u 1.8 4u 1.8)",
                      f".ic v(out_base)={membrane_state_v:g} v(sum_base)={VCM}"]
        base_init_node, base_type = "initlvl_base", "sky130_sc_charge_integrator_held" if use_held else "sky130_sc_charge_integrator"
    else:
        base_lines = ["Vbn_base vbiasn_base 0 0.65", "Vbp_base vbiasp_base 0 0.75", f"Vinitlvl_base initlvl_base 0 {VCM}",
                      "Vinit_base init_base 0 0", "Vinitb_base initb_base 0 1.8", f".ic v(out_base)={membrane_state_v-VCM} v(sum_base)={VCM}"]
        base_init_node, base_type = "vcm", "sky130_sc_charge_integrator"
    if use_retention_packet:
        base_amp_phase = ("PWL(0 0 4.999m 0 5m 1.8 5.0025m 1.8 5.00251m 0 5.005m 0)", "PWL(0 1.8 4.999m 1.8 5m 0 5.0025m 0 5.00251m 1.8 5.005m 1.8)")
        base_conn = "PWL(0 0 4.999m 0 5m 1.8 5.0025m 1.8 5.00251m 0 5.005m 0)"
        base_connb = "PWL(0 1.8 4.999m 1.8 5m 0 5.0025m 0 5.00251m 1.8 5.005m 1.8)"
    elif use_retention:
        base_amp_phase = ("PWL(0 0 8u 0 8.001u 0 5.005m 0)", "PWL(0 1.8 8u 1.8 8.001u 1.8 5.005m 1.8)")
        base_conn = "PWL(0 0 8u 0 8.001u 0 5.005m 0)"
        base_connb = "PWL(0 1.8 8u 1.8 8.001u 1.8 5.005m 1.8)"
    elif use_held:
        base_amp_phase = ("PWL(0 0 2.999u 0 3u 1.8 4.999u 1.8 5u 0 8u 0)", "PWL(0 1.8 2.999u 1.8 3u 0 4.999u 0 5u 1.8 8u 1.8)")
        base_conn = "PWL(0 0 2.999u 0 3u 1.8 4.999u 1.8 5u 0 8u 0)"
        base_connb = "PWL(0 1.8 2.999u 1.8 3u 0 4.999u 0 5u 1.8 8u 1.8)"
    else:
        base_amp_phase = ("PWL(0 0 0.499u 0 0.5u 1.8 2.499u 1.8 2.5u 0 4u 0)", "PWL(0 1.8 0.499u 1.8 0.5u 0 2.499u 0 2.5u 1.8 4u 1.8)")
        base_conn = "PWL(0 0 0.499u 0 0.5u 1.8 2.499u 1.8 2.5u 0 4u 0)"
        base_connb = "PWL(0 1.8 0.499u 1.8 0.5u 0 2.499u 0 2.5u 1.8 4u 1.8)"
    lines += [
        *base_lines,
        "Vreset_base reset_base 0 0", "Vresetb_base resetb_base 0 1.8",
        "Vpacket_reset_base packet_reset_base 0 0", "Vpacket_resetb_base packet_resetb_base 0 1.8",
        f"Vconn_base conn_base 0 {base_conn}",
        f"Vconnb_base connb_base 0 {base_connb}",
        f"Vamp_base amp_base 0 {base_amp_phase[0]}",
        f"Vampb_base ampb_base 0 {base_amp_phase[1]}",
        f"Vpkt_base ptop_base 0 {VCM}",
        f"Xcell_base out_base sum_base ptop_base pbot_base reset_base resetb_base packet_reset_base packet_resetb_base {base_init_node} init_base initb_base conn_base connb_base " + ("amp_base ampb_base " if use_held else "") + f"vbiasn_base vbiasp_base vdd 0 vcm {base_type} cmem_um=100 cpacket_um={cap_um:g}",
    ]
    vectors += ["v(out_base)", "v(sum_base)"]
    data = RES / "sky130_sc_packet_amplitude.dat"
    lines += [".control", "set wr_singlescale", "set wr_vecnames", f"tran {tran_step} {sim_stop_s} uic", f"wrdata ../results/{data.name} {' '.join(vectors)}", "quit", ".endc", ".end"]
    deck = BENCH / "sky130_sc_packet_amplitude.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", "60", "ngspice", "-b", deck.name]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=75)
    log = proc.stdout + proc.stderr
    (RES / "sky130_sc_packet_amplitude.log").write_text(log, encoding="utf-8")
    rows = []
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(x) for x in line.split()])
            except ValueError: pass
    report: dict[str, object] = {"test": "sky130_tt_1um_packet_top_plate_swing", "simulation_completed": proc.returncode == 0 and bool(rows), "exit_code": proc.returncode, "cases": cases}
    if report["simulation_completed"] and len(rows[-1]) == 1 + 2*len(cases) + 2:
        base_j = 1 + 2*len(cases)
        base_pre = min(rows, key=lambda r: abs(r[0]-pre_sample_s))[base_j]
        base_post = min(rows, key=lambda r: abs(r[0]-post_sample_s))[base_j]
        for i, case in enumerate(cases):
            j = 1+2*i
            pre = min(rows, key=lambda r: abs(r[0]-pre_sample_s))[j]
            post = min(rows, key=lambda r: abs(r[0]-post_sample_s))[j]
            case.update({"initial_state_v": pre, "final_state_v": post, "raw_state_change_v": post-pre,
                         "requested_initial_membrane_state_v": membrane_state_v,
                         "initial_state_error_v": pre-membrane_state_v,
                         "physical_init_state_v": min(rows, key=lambda r: abs(r[0]-init_sample_s))[j],
                         "physical_init_state_error_v": min(rows, key=lambda r: abs(r[0]-init_sample_s))[j]-membrane_state_v,
                         "idle_retention_error_v": post-pre if use_retention else None,
                         "no_event_control_change_v": base_post-base_pre,
                         "state_change_v": (post-pre)-(base_post-base_pre)})
        report.update({"trace_finite": all(all(__import__('math').isfinite(v) for v in row) for row in rows), "max_virtual_sum_error_v": max(abs(min(rows,key=lambda r:abs(r[0]-post_sample_s))[2+2*i]-VCM) for i in range(len(cases))), "scope": "one 1um MIM packet, one 0.3V-class membrane at VCM, seven input precharge amplitudes, both signs, TT schematic; no mismatch, PVT, extracted routing or multievent effects"})
    else:
        report["log_tail"] = log[-3000:]
    (RES / "sky130_sc_packet_amplitude.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"report": str(RES / "sky130_sc_packet_amplitude.json"), "simulation_completed": report["simulation_completed"], "cases": cases}, indent=2))
    return 0 if report["simulation_completed"] and report.get("trace_finite", False) else 2

if __name__ == "__main__":
    raise SystemExit(main())

