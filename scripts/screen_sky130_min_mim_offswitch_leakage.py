"""Screen compact MIM off-switch leakage, optional shared read, and hold time."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
REDUCED_PAIR = BENCH / "sky130_min_mim_pair_pex_reducedmim_subground.spice"
STANDARD_PAIR = BENCH / "sky130_min_mim_pair_pex_standard_subground.spice"
TG = "/workspace/artifacts/analog_asic/layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"
MOSCAP = "/workspace/artifacts/analog_asic/layout/sky130_moscap_pcell_probe_10x1_nf1/moscap_pcell_probe.spice"
READ_MIM = "/workspace/artifacts/analog_asic/layout/sky130_mim_membrane_10x10_m3_2/membrane_cap_mim_10x10um.spice"
READ_BANK_PEX = ROOT / "artifacts/analog_asic/layout/sky130_shared_read_mim_bank_5x10x10/shared_read_mim_bank_5x10x10_pex.spice"
LIB = "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice"
IMAGE = "eventspikeseg:analog-ngspice36"
KINDS = ("bare", "routed_tg", "n_l0p5", "n_l2", "n_l8", "p_l0p5", "p_l2", "p_l8", "tg_l0p5")


def main() -> None:
    reduced_mim = "--standard-mim" not in sys.argv[1:]
    corner = sys.argv[sys.argv.index("--corner") + 1].lower() if "--corner" in sys.argv else "ss"
    if corner not in ("tt", "ss", "ff"):
        raise ValueError("corner must be tt, ss or ff")
    temp_c = float(sys.argv[sys.argv.index("--temp-c") + 1]) if "--temp-c" in sys.argv else {"tt": 27, "ss": 0, "ff": 85}[corner]
    end_ms = float(sys.argv[sys.argv.index("--end-ms") + 1]) if "--end-ms" in sys.argv else 5.0
    if not 0.03 <= end_ms <= 5:
        raise ValueError("--end-ms must be within [0.03, 5] ms")
    read_ms = end_ms - 0.01
    pre_ms = end_ms - 0.02
    bank_pre_ms = end_ms - 0.016
    bank_enable_ms = end_ms - 0.015
    p_width_factor = float(sys.argv[sys.argv.index("--p-width-factor") + 1]) if "--p-width-factor" in sys.argv else 1.0
    if not 0.8 <= p_width_factor <= 1.2:
        raise ValueError("p-width factor must be within [0.8, 1.2]")
    offset_mv = float(sys.argv[sys.argv.index("--offset-mv") + 1]) if "--offset-mv" in sys.argv else 300.0
    reverse_state = "--reverse-state" in sys.argv
    source_mode = sys.argv[sys.argv.index("--source-mode") + 1] if "--source-mode" in sys.argv else "parked"
    if source_mode not in ("parked", "vcm"):
        raise ValueError("source mode must be parked or vcm")
    if not 0 <= offset_mv <= 900:
        raise ValueError("offset must be within [0, 900] mV")
    low_v, high_v = 0.9 - offset_mv * 1e-3, 0.9 + offset_mv * 1e-3
    if reverse_state:
        low_v, high_v = high_v, low_v
    kinds = ("bare", "routed_tg", "routed_body_both", "body_both") if p_width_factor != 1.0 or corner != "ss" else (
        ("bare", "routed_tg", "routed_stacked_tg", "routed_body_both", "tg_l0p5", "tg_l8", "body_n", "body_p", "body_both")
        if offset_mv != 300.0 else KINDS)
    if "--compact" in sys.argv:
        kinds = ("bare", "routed_tg")
    physical_moscap = "--physical-moscap" in sys.argv
    precharged_series = "--precharged-series" in sys.argv
    if precharged_series:
        if "--compact" not in sys.argv:
            raise ValueError("--precharged-series requires --compact")
        kinds += (("routed_stacked_precharged", "routed_stacked_precharged_moscap")
                  if physical_moscap else ("routed_stacked_precharged",))
    hv_overdrive = "--hv-overdrive" in sys.argv
    hv_body_currents = "--hv-body-currents" in sys.argv
    if hv_body_currents and not hv_overdrive:
        raise ValueError("--hv-body-currents requires --hv-overdrive")
    hv_overdrive_v = float(sys.argv[sys.argv.index("--hv-overdrive-v") + 1]) if "--hv-overdrive-v" in sys.argv else 0.5
    if not 0 <= hv_overdrive_v <= 1.5:
        raise ValueError("--hv-overdrive-v must be within [0, 1.5] V")
    if hv_overdrive:
        if "--compact" not in sys.argv or not physical_moscap:
            raise ValueError("--hv-overdrive requires --compact --physical-moscap")
        kinds += ("hv_tg_moscap", "hv_tg_overdrive_moscap",
                  "hv_n_overdrive_moscap", "hv_p_overdrive_moscap",
                  "hv_asym_overdrive_moscap")
    shared_read = "--shared-read" in sys.argv
    ideal_read_switch = "--ideal-read-switch" in sys.argv
    if ideal_read_switch and not shared_read:
        raise ValueError("--ideal-read-switch requires --shared-read")
    schematic_min_read_switch = "--schematic-min-read-switch" in sys.argv
    if schematic_min_read_switch and (not shared_read or ideal_read_switch):
        raise ValueError("--schematic-min-read-switch requires --shared-read without --ideal-read-switch")
    read_input_w_um = float(sys.argv[sys.argv.index("--read-input-w-um") + 1]) if "--read-input-w-um" in sys.argv else 10.0
    read_input_cap_ff = float(sys.argv[sys.argv.index("--read-input-cap-ff") + 1]) if "--read-input-cap-ff" in sys.argv else 0.0
    read_mim_units = int(sys.argv[sys.argv.index("--read-mim-units") + 1]) if "--read-mim-units" in sys.argv else 0
    physical_read_bank = "--physical-read-bank" in sys.argv
    range_select = sys.argv[sys.argv.index("--range-select") + 1] if "--range-select" in sys.argv else "direct"
    if range_select not in ("direct", "low", "high") or (range_select != "direct" and not physical_read_bank):
        raise ValueError("--range-select must be direct, low, or high; low/high require --physical-read-bank")
    if not 0.42 <= read_input_w_um <= 10:
        raise ValueError("read input width must be within [0.42, 10] um")
    if not 0 <= read_input_cap_ff <= 10000 or (read_input_cap_ff and not shared_read):
        raise ValueError("read input cap must be within [0, 10000] fF and requires --shared-read")
    if not 0 <= read_mim_units <= 20 or (read_mim_units and (not shared_read or read_input_cap_ff)):
        raise ValueError("read MIM units must be within [0, 20] and requires --shared-read without ideal input cap")
    if physical_read_bank and (not shared_read or read_input_cap_ff or read_mim_units):
        raise ValueError("physical read bank requires --shared-read without alternate input capacitor")
    if physical_moscap:
        if "--compact" not in sys.argv:
            raise ValueError("--physical-moscap requires --compact for a bounded comparison")
        kinds += ("routed_tg_moscap",)
    if shared_read:
        if not physical_moscap:
            raise ValueError("--shared-read requires --physical-moscap")
        kinds += ("routed_tg_moscap_read",)
    with_sensor = "--with-sensor" in sys.argv
    sensor_tail_bias_v = float(sys.argv[sys.argv.index("--sensor-tail-bias-v") + 1]) if "--sensor-tail-bias-v" in sys.argv else 0.70
    sensor_vdd_v = float(sys.argv[sys.argv.index("--sensor-vdd-v") + 1]) if "--sensor-vdd-v" in sys.argv else 1.8
    sensor_enable_at_ms = float(sys.argv[sys.argv.index("--sensor-enable-at-ms") + 1]) if "--sensor-enable-at-ms" in sys.argv else None
    sensor_enable_ramp_us = float(sys.argv[sys.argv.index("--sensor-enable-ramp-us") + 1]) if "--sensor-enable-ramp-us" in sys.argv else 0.01
    if not 0 <= sensor_tail_bias_v <= 1.8:
        raise ValueError("sensor tail bias must be within [0, 1.8] V")
    if not 0 <= sensor_vdd_v <= 1.8:
        raise ValueError("sensor supply must be within [0, 1.8] V")
    if sensor_enable_at_ms is not None and (not with_sensor or not 0.01 < sensor_enable_at_ms < end_ms):
        raise ValueError("sensor enable time requires --with-sensor and must precede --end-ms")
    if not 0 < sensor_enable_ramp_us <= 5:
        raise ValueError("sensor enable ramp must be within (0, 5] us")
    if with_sensor:
        if "--compact" not in sys.argv:
            raise ValueError("--with-sensor requires --compact for a bounded comparison")
        kinds += ("routed_tg_sensor",)
    PAIR = REDUCED_PAIR if reduced_mim else STANDARD_PAIR
    if not PAIR.exists():
        raise RuntimeError("substrate-grounded PEX must be generated by screen_sky130_min_mim_tg_hold.py")
    model = PAIR.read_text(encoding="ascii")
    if "Vsubstrate VSUBS 0 0" not in model or (reduced_mim and "Cunit0" not in model):
        raise RuntimeError("unexpected PEX diagnostic model")
    lines = [
        "* 2x2um MIM PEX, nominal C with grounded VSUBS, off-switch leakage only",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9 method=gear maxord=2",
        f'.lib "{LIB}" {corner}',
        f'.include "/workspace/{PAIR.relative_to(ROOT).as_posix()}"',
        f'.include "{TG}"', f".temp {temp_c:g}",
        "Vcm vcm 0 0.9", "Vdd vdd 0 1.8", f"Vlow low 0 {low_v:.12g}", f"Vhigh high 0 {high_v:.12g}",
        "Vgn gn 0 0", "Vgp gp 0 1.8",
        "Vinit_en init_en 0 PWL(0 1.8 0.9u 1.8 1u 0 5.01m 0)",
        ".model ideal_init SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)",
    ]
    if physical_moscap:
        lines.append(f'.include "{MOSCAP}"')
    if hv_overdrive:
        lines += ["Vhv_ng hv_ng 0 0", "Vhv_pg hv_pg 0 1.8",
                  f"Vhv_ng_boost hv_ng_boost 0 {-hv_overdrive_v:g}",
                  f"Vhv_pg_boost hv_pg_boost 0 {1.8+hv_overdrive_v:g}"]
    if read_mim_units:
        lines.append(f'.include "{READ_MIM}"')
    if physical_read_bank:
        extracted_bank = READ_BANK_PEX.read_text(encoding="ascii")
        if ".subckt shared_read_mim_bank_5x10x10 READP READN VCM" not in extracted_bank or " SUB " not in extracted_bank:
            raise RuntimeError("unexpected read-bank PEX substrate interface")
        grounded_bank = BENCH / "sky130_shared_read_mim_bank_5x10x10_pex_subground.spice"
        grounded_bank.write_text(re.sub(r"\bSUB\b", "0", extracted_bank), encoding="ascii")
        lines.append(f'.include "/workspace/{grounded_bank.relative_to(ROOT).as_posix()}"')
    body_probes: list[str] = []
    terminal_probes: list[str] = []
    def hv_body(kind: str, side: str, device: str) -> str:
        if not hv_body_currents:
            return "0" if device == "n" else "vdd"
        node = f"body_{kind}_{side}_{device}"
        reference = "0" if device == "n" else "vdd"
        lines.append(f"V{node} {node} {reference} 0")
        body_probes.append(node)
        return node
    def hv_terminal(kind: str, side: str, device: str, terminal: str, external: str) -> str:
        if not hv_body_currents:
            return external
        node = f"term_{kind}_{side}_{device}_{terminal}"
        lines.append(f"V{node} {external} {node} 0")
        terminal_probes.append(node)
        return node
    for kind in kinds:
        low, high = f"state_{kind}_low", f"state_{kind}_high"
        lines.append(f"Xpair_{kind} vcm {low} vcm {high} sky130_differential_trim_cap_pair")
        for side, state in (("low", low), ("high", high)):
            source = "vcm" if source_mode == "vcm" else side
            lines.append(f"Sinit_{kind}_{side} {side} {state} init_en 0 ideal_init")
            if kind in ("routed_tg", "routed_tg_sensor", "routed_tg_moscap", "routed_tg_moscap_read"):
                lines.append(f"Xsw_{kind}_{side} {source} {state} gn gp vdd 0 sky130_transmission_gate_raw")
                if kind in ("routed_tg_moscap", "routed_tg_moscap_read"):
                    lines.append(f"Xcap_{kind}_{side} {state} 0 0 moscap_pcell_probe")
            elif kind == "routed_body_both":
                lines.append(f"Xsw_{kind}_{side} {source} {state} gn gp {state} {state} sky130_transmission_gate_raw")
            elif kind == "routed_stacked_tg" or kind.startswith("routed_stacked_precharged"):
                mid = f"mid_{kind}_{side}"
                if kind.startswith("routed_stacked_precharged"):
                    lines.append(f"Sinit_{kind}_{side}_mid {side} {mid} init_en 0 ideal_init")
                lines += [f"Xsw_{kind}_{side}_a {source} {mid} gn gp vdd 0 sky130_transmission_gate_raw",
                          f"Xsw_{kind}_{side}_b {mid} {state} gn gp vdd 0 sky130_transmission_gate_raw"]
                if kind == "routed_stacked_precharged_moscap":
                    lines.append(f"Xcap_{kind}_{side} {state} 0 0 moscap_pcell_probe")
            elif kind in ("hv_tg_moscap", "hv_tg_overdrive_moscap"):
                ng, pg = (("hv_ng_boost", "hv_pg_boost") if kind == "hv_tg_overdrive_moscap"
                          else ("hv_ng", "hv_pg"))
                nb, pb = hv_body(kind, side, "n"), hv_body(kind, side, "p")
                ns = hv_terminal(kind, side, "n", "source", source)
                nd = hv_terminal(kind, side, "n", "state", state)
                ps = hv_terminal(kind, side, "p", "source", source)
                pd = hv_terminal(kind, side, "p", "state", state)
                lines += [f"Xsw_n_{kind}_{side} {ns} {ng} {nd} {nb} sky130_fd_pr__nfet_g5v0d10v5 w=1 l=0.5",
                          f"Xsw_p_{kind}_{side} {ps} {pg} {pd} {pb} sky130_fd_pr__pfet_g5v0d10v5 w=1 l=0.5",
                          f"Xcap_{kind}_{side} {state} 0 0 moscap_pcell_probe"]
            elif kind in ("hv_n_overdrive_moscap", "hv_p_overdrive_moscap",
                          "hv_asym_overdrive_moscap"):
                use_n = kind.startswith("hv_n_") or (kind == "hv_asym_overdrive_moscap" and side == "low")
                if use_n:
                    nb = hv_body(kind, side, "n")
                    ns = hv_terminal(kind, side, "n", "source", source)
                    nd = hv_terminal(kind, side, "n", "state", state)
                    lines.append(f"Xsw_{kind}_{side} {ns} hv_ng_boost {nd} {nb} sky130_fd_pr__nfet_g5v0d10v5 w=1 l=0.5")
                else:
                    pb = hv_body(kind, side, "p")
                    ps = hv_terminal(kind, side, "p", "source", source)
                    pd = hv_terminal(kind, side, "p", "state", state)
                    lines.append(f"Xsw_{kind}_{side} {ps} hv_pg_boost {pd} {pb} sky130_fd_pr__pfet_g5v0d10v5 w=1 l=0.5")
                lines.append(f"Xcap_{kind}_{side} {state} 0 0 moscap_pcell_probe")
            elif kind.startswith("n_l"):
                length = kind.split("l", 1)[1].replace("p", ".")
                lines.append(f"Xsw_{kind}_{side} {source} gn {state} 0 sky130_fd_pr__nfet_01v8 w=0.42 l={length}")
            elif kind.startswith("p_l"):
                length = kind.split("l", 1)[1].replace("p", ".")
                lines.append(f"Xsw_{kind}_{side} {source} gp {state} vdd sky130_fd_pr__pfet_01v8 w=0.84 l={length}")
            elif kind in ("tg_l0p5", "tg_l8"):
                length = 0.5 if kind == "tg_l0p5" else 8
                lines += [f"Xsw_n_{kind}_{side} {source} gn {state} 0 sky130_fd_pr__nfet_01v8 w=0.42 l={length}",
                          f"Xsw_p_{kind}_{side} {source} gp {state} vdd sky130_fd_pr__pfet_01v8 w=0.84 l={length}"]
            elif kind.startswith("body_"):
                n_body = state if kind in ("body_n", "body_both") else "0"
                p_body = state if kind in ("body_p", "body_both") else "vdd"
                lines += [f"Xsw_n_{kind}_{side} {source} gn {state} {n_body} sky130_fd_pr__nfet_01v8 w=0.42 l=0.5",
                          f"Xsw_p_{kind}_{side} {source} gp {state} {p_body} sky130_fd_pr__pfet_01v8 w={0.84*p_width_factor:g} l=0.5"]
    if with_sensor:
        ramp_end_ms = sensor_enable_at_ms + sensor_enable_ramp_us * 0.001 if sensor_enable_at_ms is not None else None
        sensor_vdd_source = (f"PWL(0 0 {sensor_enable_at_ms:g}m 0 {ramp_end_ms:g}m {sensor_vdd_v:g} 5.01m {sensor_vdd_v:g})"
                             if sensor_enable_at_ms is not None else f"{sensor_vdd_v:g}")
        sensor_tail_source = (f"PWL(0 0 {sensor_enable_at_ms:g}m 0 {ramp_end_ms:g}m {sensor_tail_bias_v:g} 5.01m {sensor_tail_bias_v:g})"
                              if sensor_enable_at_ms is not None else f"{sensor_tail_bias_v:g}")
        lines += [
            f"Vsensor_supply sensor_vdd 0 {sensor_vdd_source}",
            f"Vtail_sensor tailbias_sensor 0 {sensor_tail_source}",
            "Xsn1 outp_sensor state_routed_tg_sensor_high tail_sensor 0 sky130_fd_pr__nfet_01v8 w=10 l=1",
            "Xsn2 outn_sensor state_routed_tg_sensor_low tail_sensor 0 sky130_fd_pr__nfet_01v8 w=10 l=1",
            "Xst tail_sensor tailbias_sensor 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2",
            "Xsp1 outp_sensor outp_sensor sensor_vdd sensor_vdd sky130_fd_pr__pfet_01v8 w=20 l=1",
            "Xsp2 outn_sensor outp_sensor sensor_vdd sensor_vdd sky130_fd_pr__pfet_01v8 w=20 l=1",
            "Rslp outp_sensor 0 100k", "Rsln outn_sensor 0 100k",
        ]
    if shared_read:
        lines += [
            f"Vread_en read_en 0 PWL(0 0 {read_ms-0.001:g}m 0 {read_ms:g}m 1.8 5.01m 1.8)",
            f"Vread_enb read_enb 0 PWL(0 1.8 {read_ms-0.001:g}m 1.8 {read_ms:g}m 0 5.01m 0)",
            f"Vpre_en pre_en 0 PWL(0 1.8 {pre_ms-0.001:g}m 1.8 {pre_ms:g}m 0 5.01m 0)",
            "Spre_high vcm sense_high pre_en 0 ideal_init",
            "Spre_low vcm sense_low pre_en 0 ideal_init",
            "Vsupply_read sensor_read_vdd 0 1.8",
            "Vtail_read tailbias_read 0 0.7",
            f"Xrn1 outp_read sense_high tail_read 0 sky130_fd_pr__nfet_01v8 w={read_input_w_um:g} l=1",
            f"Xrn2 outn_read sense_low tail_read 0 sky130_fd_pr__nfet_01v8 w={read_input_w_um:g} l=1",
            "Xrt tail_read tailbias_read 0 0 sky130_fd_pr__nfet_01v8 w=10 l=2",
            "Xrp1 outp_read outp_read sensor_read_vdd sensor_read_vdd sky130_fd_pr__pfet_01v8 w=20 l=1",
            "Xrp2 outn_read outp_read sensor_read_vdd sensor_read_vdd sky130_fd_pr__pfet_01v8 w=20 l=1",
            "Rrp outp_read 0 100k", "Rrn outn_read 0 100k",
        ]
        if read_input_cap_ff:
            lines += [f"Cread_high sense_high vcm {read_input_cap_ff:g}f",
                      f"Cread_low sense_low vcm {read_input_cap_ff:g}f"]
        if read_mim_units:
            for side in ("high", "low"):
                lines += [f"Xread_mim_{side}_{index} sense_{side} vcm membrane_cap_mim_10x10um"
                          for index in range(read_mim_units)]
        if physical_read_bank:
            if range_select == "direct":
                lines.append("Xread_bank sense_high sense_low vcm shared_read_mim_bank_5x10x10")
            else:
                lines += [
                    "Xread_bank bank_high bank_low vcm shared_read_mim_bank_5x10x10",
                    f"Vbank_pre_en bank_pre_en 0 PWL(0 1.8 {bank_pre_ms-0.001:g}m 1.8 {bank_pre_ms:g}m 0 5.01m 0)",
                    "Sbank_pre_high vcm bank_high bank_pre_en 0 ideal_init",
                    "Sbank_pre_low vcm bank_low bank_pre_en 0 ideal_init",
                    (f"Vbank_en bank_en 0 PWL(0 0 {bank_enable_ms-0.001:g}m 0 {bank_enable_ms:g}m 1.8 5.01m 1.8)"
                     if range_select == "high" else "Vbank_en bank_en 0 0"),
                    (f"Vbank_enb bank_enb 0 PWL(0 1.8 {bank_enable_ms-0.001:g}m 1.8 {bank_enable_ms:g}m 0 5.01m 0)"
                     if range_select == "high" else "Vbank_enb bank_enb 0 1.8"),
                    "Xbank_sel_high sense_high bank_high bank_en bank_enb vdd 0 sky130_transmission_gate_raw",
                    "Xbank_sel_low sense_low bank_low bank_en bank_enb vdd 0 sky130_transmission_gate_raw",
                ]
        if ideal_read_switch:
            lines += [".model ideal_read SW(Ron=10 Roff=1e30 Vt=0.9 Vh=0.1)",
                      "Sread_high state_routed_tg_moscap_read_high sense_high read_en 0 ideal_read",
                      "Sread_low state_routed_tg_moscap_read_low sense_low read_en 0 ideal_read"]
        elif schematic_min_read_switch:
            for side in ("high", "low"):
                state = f"state_routed_tg_moscap_read_{side}"
                sense = f"sense_{side}"
                lines += [f"Xread_n_{side} {sense} read_en {state} 0 sky130_fd_pr__nfet_01v8 w=0.42 l=0.15",
                          f"Xread_p_{side} {sense} read_enb {state} vdd sky130_fd_pr__pfet_01v8 w=0.84 l=0.15"]
        else:
            lines += ["Xread_high state_routed_tg_moscap_read_high sense_high read_en read_enb vdd 0 sky130_transmission_gate_raw",
                      "Xread_low state_routed_tg_moscap_read_low sense_low read_en read_enb vdd 0 sky130_transmission_gate_raw"]
    lines += [".control", "set numdgt=15", f"tran 1u {end_ms:g}m"]
    for kind in kinds:
        for side in ("low", "high"):
            lines += [f"meas tran {kind}_{side}_start find v(state_{kind}_{side}) at=2u",
                      f"meas tran {kind}_{side}_end find v(state_{kind}_{side}) at={end_ms:g}m"]
    if with_sensor:
        lines += [f"meas tran sensor_outp_end find v(outp_sensor) at={end_ms:g}m",
                  f"meas tran sensor_outn_end find v(outn_sensor) at={end_ms:g}m",
                  f"meas tran sensor_supply_current_end find i(Vsensor_supply) at={end_ms:g}m"]
    if sensor_enable_at_ms is not None:
        lines += [f"meas tran sensor_low_pre_enable find v(state_routed_tg_sensor_low) at={sensor_enable_at_ms-0.001:g}m",
                  f"meas tran sensor_high_pre_enable find v(state_routed_tg_sensor_high) at={sensor_enable_at_ms-0.001:g}m"]
    if shared_read:
        lines += [
            f"meas tran read_low_before find v(state_routed_tg_moscap_read_low) at={read_ms-0.002:g}m",
            f"meas tran read_high_before find v(state_routed_tg_moscap_read_high) at={read_ms-0.002:g}m",
            f"meas tran read_low_end find v(state_routed_tg_moscap_read_low) at={end_ms:g}m",
            f"meas tran read_high_end find v(state_routed_tg_moscap_read_high) at={end_ms:g}m",
            f"meas tran read_outp_before find v(outp_read) at={read_ms-0.002:g}m",
            f"meas tran read_outn_before find v(outn_read) at={read_ms-0.002:g}m",
            f"meas tran read_outp_end find v(outp_read) at={end_ms:g}m",
            f"meas tran read_outn_end find v(outn_read) at={end_ms:g}m",
        ]
    if hv_body_currents:
        for node in body_probes + terminal_probes:
            lines.append(f"meas tran {node}_current_end find i(V{node}) at={end_ms:g}m")
    lines += ["quit", ".endc", ".end", ""]
    stem = f"sky130_min_mim_offswitch_leakage_{corner}_temp{temp_c:g}" + ("" if reduced_mim else "_standardmim")
    if end_ms != 5:
        stem += f"_end{end_ms:g}ms"
    if offset_mv != 300.0:
        stem += f"_offset{offset_mv:g}mv"
    if reverse_state:
        stem += "_reversed"
    if p_width_factor != 1.0:
        stem += f"_pwidth{p_width_factor:g}x"
    if source_mode == "vcm":
        stem += "_sourcevcm"
    if physical_moscap:
        stem += "_physicalmoscap"
    if precharged_series:
        stem += "_prechargedseries"
    if hv_overdrive:
        stem += "_hvoverdrive"
        if hv_overdrive_v != 0.5:
            stem += f"{hv_overdrive_v:g}v"
        if hv_body_currents:
            stem += "_bodycurrents"
    if shared_read:
        stem += "_sharedread"
        if read_input_w_um != 10:
            stem += f"_inputw{read_input_w_um:g}um"
        if read_input_cap_ff:
            stem += f"_inputcap{read_input_cap_ff:g}ff"
        if read_mim_units:
            stem += f"_readmim{read_mim_units}u"
        if physical_read_bank:
            stem += "_physicalreadbank"
            if range_select != "direct":
                stem += f"_rangeselect{range_select}"
        if ideal_read_switch:
            stem += "_idealswitch"
        if schematic_min_read_switch:
            stem += "_schemminswitch"
    if with_sensor:
        stem += "_sensor"
        if sensor_enable_at_ms is not None:
            stem += f"_enable{sensor_enable_at_ms:g}ms"
            if sensor_enable_ramp_us != 0.01:
                stem += f"_ramp{sensor_enable_ramp_us:g}us"
            if sensor_tail_bias_v != 0.70:
                stem += f"_targettail{sensor_tail_bias_v:g}v"
            if sensor_vdd_v != 1.8:
                stem += f"_targetvdd{sensor_vdd_v:g}v"
        elif sensor_tail_bias_v != 0.70:
            stem += f"_tail{sensor_tail_bias_v:g}v"
        if sensor_enable_at_ms is None and sensor_vdd_v != 1.8:
            stem += f"_supply{sensor_vdd_v:g}v"
    path = BENCH / f"{stem}.cir"
    path.write_text("\n".join(lines), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", IMAGE, "180", "ngspice", "-b",
           f"/workspace/{path.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=195, cwd=ROOT)
    log = proc.stdout + proc.stderr
    (RESULTS / f"{stem}.log").write_text(log, encoding="utf-8")
    values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*([a-z0-9_]+_(?:low|high)_(?:start|end))\s*=\s*([-+0-9.eE]+)", log)
        if not key.lower().startswith("read_")}
    sensor_values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(sensor_out[pn]_end)\s*=\s*([-+0-9.eE]+)", log)}
    sensor_supply_match = re.search(r"(?im)^\s*sensor_supply_current_end\s*=\s*([-+0-9.eE]+)", log)
    pre_enable_values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(sensor_(?:low|high)_pre_enable)\s*=\s*([-+0-9.eE]+)", log)}
    read_values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(read_(?:low|high|outp|outn)_(?:before|end))\s*=\s*([-+0-9.eE]+)", log)}
    body_values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(body_[a-z0-9_]+_current_end)\s*=\s*([-+0-9.eE]+)", log)}
    terminal_values = {key.lower(): float(value) for key, value in re.findall(
        r"(?im)^\s*(term_[a-z0-9_]+_current_end)\s*=\s*([-+0-9.eE]+)", log)}
    complete = (proc.returncode == 0 and "ngspice-36 done" in log and len(values) == 4 * len(kinds)
                and (not with_sensor or (len(sensor_values) == 2 and sensor_supply_match is not None))
                and (sensor_enable_at_ms is None or len(pre_enable_values) == 2)
                and (not shared_read or len(read_values) == 8))
    complete = complete and (not hv_body_currents or
                             (len(body_values) == len(body_probes)
                              and len(terminal_values) == len(terminal_probes)))
    if complete:
        start_tolerance_v = max(1e-6, min(0.03, offset_mv * 0.0005))
        complete = all(abs(values[f"{kind}_low_start"] - low_v) < start_tolerance_v
                       and abs(values[f"{kind}_high_start"] - high_v) < start_tolerance_v
                       for kind in kinds)
    cases = []
    if complete:
        for kind in kinds:
            cases.append({
                "switch": kind,
                "low_start_v": values[f"{kind}_low_start"],
                "low_end_v": values[f"{kind}_low_end"],
                "high_start_v": values[f"{kind}_high_start"],
                "high_end_v": values[f"{kind}_high_end"],
                "low_drift_mv": (values[f"{kind}_low_end"] - values[f"{kind}_low_start"]) * 1e3,
                "high_drift_mv": (values[f"{kind}_high_end"] - values[f"{kind}_high_start"]) * 1e3,
            })
    report = {
        "test": "sky130_minimum_mim_offswitch_leakage_isolation",
        "simulation_completed": complete, "return_code": proc.returncode,
        "corner": corner.upper(), "temperature_c": temp_c,
        "transient_end_ms": end_ms, "read_connection_at_ms": read_ms if shared_read else None,
        "commanded_state_offset_from_vcm_mv": offset_mv,
        "reversed_state_polarity": reverse_state,
        "off_switch_source_mode": source_mode,
        "sensor_attached": with_sensor,
        "physical_moscap_attached": physical_moscap,
        "precharged_series_isolation": precharged_series,
        "hv_overdrive_screen": hv_overdrive,
        "hv_off_gate_overdrive_v": hv_overdrive_v if hv_overdrive else None,
        "hv_body_current_probes_enabled": hv_body_currents,
        "hv_body_current_end_a": body_values if hv_body_currents else None,
        "hv_terminal_current_end_a": terminal_values if hv_body_currents else None,
        "shared_read_attached": shared_read,
        "ideal_read_switch": ideal_read_switch,
        "schematic_min_read_switch": schematic_min_read_switch,
        "shared_read_input_width_um": read_input_w_um if shared_read else None,
        "shared_read_input_cap_ff": read_input_cap_ff if shared_read else None,
        "shared_read_10x10_mim_units_per_rail": read_mim_units if shared_read else None,
        "shared_read_physical_mim_bank": physical_read_bank,
        "shared_read_range_select": range_select if shared_read else None,
        "sensor_tail_bias_v": sensor_tail_bias_v if with_sensor else None,
        "sensor_supply_voltage_v": sensor_vdd_v if with_sensor else None,
        "sensor_enable_at_ms": sensor_enable_at_ms,
        "sensor_enable_ramp_us": sensor_enable_ramp_us if sensor_enable_at_ms is not None else None,
        "p_width_factor_for_body_variants": p_width_factor,
        "mim": "DRC/LVS routed 2x2um pair PEX, explicitly grounded extracted VSUBS; " +
               ("nominal-cap ESR reduction" if reduced_mim else "unmodified PDK MIM series model"),
        "reduced_mim_internal_series_rc": reduced_mim,
        "initialization": "ideal 10ohm programming switch opens at1us; physical access device remains off; measurement starts2us",
        "cases": cases,
        "sensor_end_outputs_v": sensor_values if with_sensor else None,
        "sensor_supply_current_end_a": float(sensor_supply_match.group(1)) if sensor_supply_match else None,
        "sensor_pre_enable_state_v": pre_enable_values if sensor_enable_at_ms is not None else None,
        "shared_read_values_v": read_values if shared_read else None,
        "limitations": "Diagnostic PEX correction, schematic sensor/body-biased and HV switch variants except the separately extracted routed TG and optional MOSCAP; no real programming, calibrated readout, noise/mismatch, event injection or full-chip service. HV zero-volt body/source/state probes are schematic model diagnostics, not physical terminal-current measurements. Source mode vcm fixes the off-switch bus at 0.9V; parked mode holds it at the cell's initial commanded state and is an optimistic control. Body-to-state cases are electrical screens only: each NFET would require an isolated p-well/deep n-well, and well junction leakage, tap/guard-ring area, DRC/LVS and latchup are not included here.",
    }
    (RESULTS / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not complete:
        raise RuntimeError(f"incomplete ngspice run: {log[-2500:]}")


if __name__ == "__main__":
    main()
