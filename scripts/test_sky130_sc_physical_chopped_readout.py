"""Bounded physical membrane test using ABBA phase-swapped OTA readout."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from test_sky130_sc_physical_accumulation import COMMON, RES, BENCH, cell

ROOT = Path(__file__).resolve().parents[1]
HEADER = r"""* SKY130 physical membranes with ABBA chopped buffered readout
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    import sys
    seq = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--sequence=")), "pn")
    rf_length = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--rf-length=")), "3078"))
    threshold_uv = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--threshold-offset-uv=")), "0"))
    packet_step_v = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--packet-step-v=")), "0.3"))
    membrane_cap_um = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--membrane-cap-um=")), "100"))
    packet_cap_um = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--packet-cap-um=")), "1"))
    positive_packet_step_v = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--positive-packet-step-v=")), str(packet_step_v)))
    negative_packet_step_v = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--negative-packet-step-v=")), str(packet_step_v)))
    early_positive_scale = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--early-positive-scale=")), "1"))
    early_negative_scale = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--early-negative-scale=")), "1"))
    early_event_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--early-event-us=")), "500"))
    late_event_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--late-event-us=")), "4500"))
    multi_event_count = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--multi-events=")), "0"))
    multi_event_polarity = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--multi-polarity=")), "p")
    threshold_dac_code = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--threshold-dac-code=")), "-1"))
    max_step_ns = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--max-step-ns=")), "10"))
    timeout_s = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--timeout-s=")), "180"))
    init_duration_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--init-duration-us=")), "2.5"))
    threshold_drive_r = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--threshold-drive-r-ohm=")), "1"))
    threshold_drive_mode = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--threshold-drive-mode=")), "direct")
    threshold_buffer_scale = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--threshold-buffer-scale=")), "1"))
    initial_precharge_us = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--initial-precharge-us=")), "0"))
    invert_packet_polarity = "--invert-packet-polarity" in sys.argv
    differential_packet = "--differential-packet" in sys.argv
    passive_packet = "--passive-packet" in sys.argv
    stacked_packet_isolation = "--stacked-packet-isolation" in sys.argv
    stacked_hold_isolation = "--stacked-hold-isolation" in sys.argv
    direct_read_buffer = "--direct-read-buffer" in sys.argv
    read_buffer_scale = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--read-buffer-scale=")), "1"))
    init_only = "--init-only" in sys.argv
    hold_threshold_reference = "--hold-threshold-reference" in sys.argv
    bipolar_charge_buckets = "--bipolar-charge-buckets" in sys.argv
    bucket_ota_always_on = "--bucket-ota-always-on" in sys.argv
    bucket_ota_always_off = "--bucket-ota-always-off" in sys.argv
    if threshold_drive_mode not in ("direct", "buffered"):
        raise ValueError("threshold-drive-mode must be direct or buffered")
    if passive_packet and differential_packet:
        raise ValueError("passive_packet and differential_packet are separate topology experiments")
    if seq not in ("pn", "np", "pp", "nn", "zz", "pz", "zp", "nz", "zn"):
        raise ValueError("sequence must be pn/np/pp/nn/zz or one-event pz/zp/nz/zn controls")
    threshold_tag = f"_dac{threshold_dac_code}" if threshold_dac_code >= 0 else (f"_th{threshold_uv:g}uv" if threshold_uv else "")
    packet_tag = f"_p{packet_step_v:g}v" if packet_step_v != 0.3 else ""
    if early_event_us != 500 or late_event_us != 4500:
        packet_tag += f"_t{early_event_us:g}_{late_event_us:g}us"
    if positive_packet_step_v != packet_step_v or negative_packet_step_v != packet_step_v:
        packet_tag += f"_pos{positive_packet_step_v:g}_neg{negative_packet_step_v:g}"
    if early_positive_scale != 1 or early_negative_scale != 1:
        packet_tag += f"_earlypos{early_positive_scale:g}_earlyneg{early_negative_scale:g}"
    step_tag=f"_s{max_step_ns:g}n" if max_step_ns != 10 else ""
    init_tag=f"_init{init_duration_us:g}u" if init_duration_us != 2.5 else ""
    pre_tag=f"_pre{initial_precharge_us:g}u" if initial_precharge_us else ""
    polarity_tag="_pinswap" if invert_packet_polarity else ""
    init_only_tag="_initonly" if init_only else ""
    holdref_tag="_holdref" if hold_threshold_reference else ""
    match_ota_tag="_matchota" if seq != "zz" and not hold_threshold_reference else ""
    buckets_tag="_bipolar" if bipolar_charge_buckets else ""
    if bucket_ota_always_on:
        buckets_tag += "_otaon"
    init_topology_tag="_heldotavcm" if threshold_dac_code >= 0 else ""
    dual_dac_tag="_singledac" if threshold_dac_code >= 0 else ""
    drive_tag=f"_{threshold_drive_mode}_drv{threshold_drive_r:g}" if threshold_dac_code >= 0 and (threshold_drive_r != 1 or threshold_drive_mode != "direct") else ""
    cap_tag = f"_cm{membrane_cap_um:g}_cp{packet_cap_um:g}" if membrane_cap_um != 100 or packet_cap_um != 1 else ""
    diff_tag = "_diffpkt" if differential_packet else ""
    passive_tag = "_passive" if passive_packet else ""
    event_gate_tag = "_eventgate" if passive_packet else ""
    multi_tag = f"_events{multi_event_count}{multi_event_polarity}" if multi_event_count else ""
    stack_tag = "_stack2" if stacked_packet_isolation else ""
    hold_stack_tag = "_holdstack2" if stacked_hold_isolation else ""
    direct_read_tag = "_directread" if direct_read_buffer else ""
    ro_scale_tag = f"_ros{read_buffer_scale:g}" if read_buffer_scale != 1 else ""
    tag = f"{seq}_abba_rf{rf_length:g}{threshold_tag}{packet_tag}{cap_tag}{diff_tag}{passive_tag}{event_gate_tag}{multi_tag}{stack_tag}{hold_stack_tag}{direct_read_tag}{ro_scale_tag}{step_tag}{init_tag}{pre_tag}{init_topology_tag}{dual_dac_tag}{polarity_tag}{holdref_tag}{match_ota_tag}{buckets_tag}{init_only_tag}{drive_tag}"
    lines = [f"SKY130 physical membrane chopped readout {tag}", COMMON, HEADER]
    signal_cell = cell(f"s_{seq}", 0.90, seq, long_bin=True, precharge=False, membrane_cap_um=membrane_cap_um, packet_cap_um=packet_cap_um)
    reference_sequence = None
    if bipolar_charge_buckets:
        signal_sequence = "".join("p" if symbol == "p" else "z" for symbol in seq)
        reference_sequence = "".join("p" if symbol == "n" else "z" for symbol in seq)
        signal_cell = cell(f"s_{seq}", 0.90, signal_sequence, long_bin=True, precharge=False, membrane_cap_um=membrane_cap_um, packet_cap_um=packet_cap_um)
        def gate_bucket_amp(cell_lines: list[str], name: str, active_mask: str) -> list[str]:
            windows = [("499u", "499.1u", "502.4u", "502.5u"),
                       ("4.499m", "4.4991m", "4.5024m", "4.5025m")]
            active = [w for i,w in enumerate(windows) if active_mask[i] != "z"]
            for j,line in enumerate(cell_lines):
                if line.startswith(f"Vamp_{name} "):
                    pts=[("0", "0")]
                    for start0,start1,end0,end1 in active:
                        pts += [(start0,"0"),(start1,"1.8"),(end0,"1.8"),(end1,"0")]
                    pts.append(("5.005m","0"))
                    cell_lines[j]=f"Vamp_{name} amp_{name} 0 PWL("+" ".join(f"{t} {v}" for t,v in pts)+")"
                elif line.startswith(f"Vampb_{name} "):
                    pts=[("0", "1.8")]
                    for start0,start1,end0,end1 in active:
                        pts += [(start0,"1.8"),(start1,"0"),(end0,"0"),(end1,"1.8")]
                    pts.append(("5.005m","1.8"))
                    cell_lines[j]=f"Vampb_{name} ampb_{name} 0 PWL("+" ".join(f"{t} {v}" for t,v in pts)+")"
            return cell_lines
        signal_cell=gate_bucket_amp(signal_cell,f"s_{seq}",signal_sequence)
        if bucket_ota_always_off:
            signal_cell=[f"Vamp_s_{seq} amp_s_{seq} 0 0" if line.startswith(f"Vamp_s_{seq} ") else line for line in signal_cell]
            signal_cell=[f"Vampb_s_{seq} ampb_s_{seq} 0 1.8" if line.startswith(f"Vampb_s_{seq} ") else line for line in signal_cell]
        if bucket_ota_always_on:
            signal_cell=[f"Vamp_s_{seq} amp_s_{seq} 0 1.8" if line.startswith(f"Vamp_s_{seq} ") else line for line in signal_cell]
            signal_cell=[f"Vampb_s_{seq} ampb_s_{seq} 0 0" if line.startswith(f"Vampb_s_{seq} ") else line for line in signal_cell]
    # Keep the packet isolation switch aligned to each packet if the event is
    # moved within the 5 ms integration interval.
    if early_event_us != 500 or late_event_us != 4500:
        def shifted_time(token: str, delta_us: float) -> str:
            value=float(token[:-1])
            if token[-1].lower()=="m": value*=1000
            elif token[-1].lower()!="u": raise ValueError(f"unsupported SPICE time token: {token}")
            return f"{value+delta_us:g}u"
        amp_points = [(0,"0"),(early_event_us-1,"0"),(early_event_us-.9,"1.8"),
                      (early_event_us+2.4,"1.8"),(early_event_us+2.5,"0"),
                      (late_event_us-1,"0"),(late_event_us-.9,"1.8"),
                      (late_event_us+2.4,"1.8"),(late_event_us+2.5,"0"),(5005,"0")]
        for idx,line in enumerate(signal_cell):
            if line.startswith(f"Vamp_s_{seq} "):
                signal_cell[idx]=f"Vamp_s_{seq} amp_s_{seq} 0 PWL("+" ".join(f"{t:g}u {v}" for t,v in amp_points)+")"
            elif line.startswith(f"Vampb_s_{seq} "):
                signal_cell[idx]=f"Vampb_s_{seq} ampb_s_{seq} 0 PWL("+" ".join(f"{t:g}u {1.8-float(v):g}" for t,v in amp_points)+")"
            elif line.startswith((f"Vconn_s_{seq} ", f"Vconnb_s_{seq} ")):
                m=re.search(r"PWL\((.*)\)",line); pts=m.group(1).split()
                for point in (2,4,6,8): pts[point]=shifted_time(pts[point],early_event_us-500)
                for point in (10,12,14,16): pts[point]=shifted_time(pts[point],late_event_us-4500)
                signal_cell[idx]=line[:m.start(1)]+" ".join(pts)+line[m.end(1):]
            elif line.startswith((f"VpacketReset_s_{seq} ", f"VpacketResetb_s_{seq} ")):
                m=re.search(r"PWL\((.*)\)",line); pts=m.group(1).split()
                for point in (2,4,6,8): pts[point]=shifted_time(pts[point],early_event_us-500)
                for point in (10,12,14,16): pts[point]=shifted_time(pts[point],late_event_us-4500)
                signal_cell[idx]=line[:m.start(1)]+" ".join(pts)+line[m.end(1):]
    init_start_us = initial_precharge_us
    init_end_us = init_start_us + init_duration_us
    for idx,line in enumerate(signal_cell):
        if line.startswith(f"Vinit_s_{seq} "):
            signal_cell[idx]=f"Vinit_s_{seq} init_s_{seq} 0 PWL(0 {1.8 if init_start_us == 0 else 0:g} {max(init_start_us-0.001,0):g}u {1.8 if init_start_us == 0 else 0:g} {init_start_us:g}u 1.8 {max(init_end_us-0.001,0):g}u 1.8 {init_end_us:g}u 0 5.005m 0)"
        elif line.startswith(f"Vinitb_s_{seq} "):
            signal_cell[idx]=f"Vinitb_s_{seq} initb_s_{seq} 0 PWL(0 {0 if init_start_us == 0 else 1.8:g} {max(init_start_us-0.001,0):g}u {0 if init_start_us == 0 else 1.8:g} {init_start_us:g}u 0 {max(init_end_us-0.001,0):g}u 0 {init_end_us:g}u 1.8 5.005m 1.8)"
    if (positive_packet_step_v != 0.3 or negative_packet_step_v != 0.3 or
            early_positive_scale != 1 or early_negative_scale != 1):
        for idx, line in enumerate(signal_cell):
            if not line.startswith(f"Vpkt_s_{seq} "):
                continue
            match = re.search(r"PWL\((.*)\)", line)
            if not match:
                raise ValueError("packet source is not a PWL waveform")
            points = match.group(1).split()
            if len(points) % 2:
                raise ValueError("malformed packet PWL point list")
            # The packet cell has two event windows. Retiming shifts each
            # complete 2 us window while preserving its 100 ns edges.
            for event_idx, point_indices, event_us in (
                (0, (2, 4, 6, 8), early_event_us),
                (1, (10, 12, 14, 16), late_event_us),
            ):
                for point in point_indices:
                    points[point] = f"{event_us + (-0.1 if point in (2, 10) else 1.9 if point in (6, 14) else 0 if point in (4, 12) else 2.0):g}u"
                point = point_indices[1]
                symbol = seq[event_idx]
                if symbol not in ("p", "n"):
                    continue
                if symbol == "p":
                    scale = early_positive_scale if event_idx == 0 else 1.0
                    step = positive_packet_step_v * scale
                    voltage = 0.9 - step if invert_packet_polarity else 0.9 + step
                else:
                    scale = early_negative_scale if event_idx == 0 else 1.0
                    step = negative_packet_step_v * scale
                    voltage = 0.9 + step if invert_packet_polarity else 0.9 - step
                points[point + 1] = f"{voltage:.12g}"
                points[point_indices[2] + 1] = f"{voltage:.12g}"
            signal_cell[idx] = line[:match.start(1)] + " ".join(points) + line[match.end(1):]
    reference = cell(f"r_{seq}", 0.90, reference_sequence if bipolar_charge_buckets else None, long_bin=True, precharge=False, membrane_cap_um=membrane_cap_um, packet_cap_um=packet_cap_um)
    if multi_event_count:
        if not passive_packet or multi_event_polarity not in ("p", "n", "altpn", "altnp"):
            raise ValueError("multi-event mode requires passive packet mode and --multi-polarity=p, n, altpn, or altnp")
        if multi_event_count < 1 or 4000.0 / max(multi_event_count - 1, 1) < 3.0:
            raise ValueError("multi-event mode supports at least one event, spaced at least 3us apart")
        event_times = [500.0 + i * 4000.0 / max(multi_event_count - 1, 1) for i in range(multi_event_count)]

        def repeated_sources(cell_lines: list[str], name: str, drive_packet: bool) -> list[str]:
            points = {
                "conn": [("0", "0")], "connb": [("0", "1.8")],
                "reset": [("0", "0")], "resetb": [("0", "1.8")],
                "amp": [("0", "0")], "ampb": [("0", "1.8")],
                "packet": [("0", "0.9")],
            }
            for event_index, event_time in enumerate(event_times):
                if multi_event_polarity in ("p", "n"): event_sign = multi_event_polarity
                elif multi_event_polarity == "altpn": event_sign = "p" if event_index % 2 == 0 else "n"
                else: event_sign = "n" if event_index % 2 == 0 else "p"
                top_step = positive_packet_step_v if event_sign == "p" else negative_packet_step_v
                top_level = 0.9 + top_step if event_sign == "p" else 0.9 - top_step
                if invert_packet_polarity: top_level = 1.8 - top_level
                points["reset"] += [(f"{event_time-1.2:g}u", "0"), (f"{event_time-1.1:g}u", "1.8"), (f"{event_time-1.0:g}u", "0")]
                points["resetb"] += [(f"{event_time-1.2:g}u", "1.8"), (f"{event_time-1.1:g}u", "0"), (f"{event_time-1.0:g}u", "1.8")]
                points["conn"] += [(f"{event_time-.9:g}u", "0"), (f"{event_time-.8:g}u", "1.8"), (f"{event_time+1.9:g}u", "1.8"), (f"{event_time+2.0:g}u", "0")]
                points["connb"] += [(f"{event_time-.9:g}u", "1.8"), (f"{event_time-.8:g}u", "0"), (f"{event_time+1.9:g}u", "0"), (f"{event_time+2.0:g}u", "1.8")]
                points["amp"] += [(f"{event_time-.9:g}u", "0"), (f"{event_time-.8:g}u", "1.8"), (f"{event_time+2.4:g}u", "1.8"), (f"{event_time+2.5:g}u", "0")]
                points["ampb"] += [(f"{event_time-.9:g}u", "1.8"), (f"{event_time-.8:g}u", "0"), (f"{event_time+2.4:g}u", "0"), (f"{event_time+2.5:g}u", "1.8")]
                packet_level = f"{top_level:g}" if drive_packet else "0.9"
                points["packet"] += [(f"{event_time-.1:g}u", "0.9"), (f"{event_time:g}u", packet_level),
                                      (f"{event_time+1.9:g}u", packet_level), (f"{event_time+2.0:g}u", "0.9")]
            for key, level in (("conn", "0"), ("connb", "1.8"), ("reset", "0"), ("resetb", "1.8"),
                               ("amp", "0"), ("ampb", "1.8"), ("packet", "0.9")):
                points[key].append(("5005u", level))
            prefixes = {"conn": f"Vconn_{name} conn_{name}", "connb": f"Vconnb_{name} connb_{name}",
                        "reset": f"VpacketReset_{name} packet_reset_{name}", "resetb": f"VpacketResetb_{name} packet_resetb_{name}",
                        "amp": f"Vamp_{name} amp_{name}", "ampb": f"Vampb_{name} ampb_{name}", "packet": f"Vpkt_{name} ptop_{name}"}
            for index, line in enumerate(cell_lines):
                for key, prefix in prefixes.items():
                    if line.startswith(prefix + " "):
                        cell_lines[index] = prefix + " 0 PWL(" + " ".join(f"{time} {value}" for time, value in points[key]) + ")"
                        break
            return cell_lines
        signal_cell = repeated_sources(signal_cell, f"s_{seq}", True)
        reference = repeated_sources(reference, f"r_{seq}", False)
    if bipolar_charge_buckets:
        reference=gate_bucket_amp(reference,f"r_{seq}",reference_sequence)
        if bucket_ota_always_off:
            reference=[f"Vamp_r_{seq} amp_r_{seq} 0 0" if line.startswith(f"Vamp_r_{seq} ") else line for line in reference]
            reference=[f"Vampb_r_{seq} ampb_r_{seq} 0 1.8" if line.startswith(f"Vampb_r_{seq} ") else line for line in reference]
        if bucket_ota_always_on:
            reference=[f"Vamp_r_{seq} amp_r_{seq} 0 1.8" if line.startswith(f"Vamp_r_{seq} ") else line for line in reference]
            reference=[f"Vampb_r_{seq} ampb_r_{seq} 0 0" if line.startswith(f"Vampb_r_{seq} ") else line for line in reference]
    for idx,line in enumerate(reference):
        if line.startswith(f"Vinit_r_{seq} "):
            reference[idx]=f"Vinit_r_{seq} init_r_{seq} 0 PWL(0 {1.8 if init_start_us == 0 else 0:g} {max(init_start_us-0.001,0):g}u {1.8 if init_start_us == 0 else 0:g} {init_start_us:g}u 1.8 {max(init_end_us-0.001,0):g}u 1.8 {init_end_us:g}u 0 5.005m 0)"
        elif line.startswith(f"Vinitb_r_{seq} "):
            reference[idx]=f"Vinitb_r_{seq} initb_r_{seq} 0 PWL(0 {0 if init_start_us == 0 else 1.8:g} {max(init_start_us-0.001,0):g}u {0 if init_start_us == 0 else 1.8:g} {init_start_us:g}u 0 {max(init_end_us-0.001,0):g}u 0 {init_end_us:g}u 1.8 5.005m 1.8)"
    if bipolar_charge_buckets and (positive_packet_step_v != 0.3 or negative_packet_step_v != 0.3):
        ref_event_v = 0.9-negative_packet_step_v if invert_packet_polarity else 0.9+negative_packet_step_v
        reference = [line.replace(" 1.2 ", f" {ref_event_v:g} ").replace(" 0.6 ", f" {ref_event_v:g} ")
                     if line.startswith(f"Vpkt_r_{seq} ") else line for line in reference]
    if threshold_dac_code >= 0 and hold_threshold_reference:
        pre_off = max(init_start_us-0.001, 0.0)
        reference = [f"Vinit_r_{seq} init_r_{seq} 0 PWL(0 0 {pre_off:g}u 0 {init_start_us:g}u 1.8 5004.999u 1.8 5.005m 1.8)"
                     if line.startswith(f"Vinit_r_{seq} ") else line for line in reference]
        reference = [f"Vinitb_r_{seq} initb_r_{seq} 0 PWL(0 1.8 {pre_off:g}u 1.8 {init_start_us:g}u 0 5004.999u 0 5.005m 0)"
                     if line.startswith(f"Vinitb_r_{seq} ") else line for line in reference]
        reference = [f"Vamp_r_{seq} amp_r_{seq} 0 0" if line.startswith(f"Vamp_r_{seq} ") else line for line in reference]
        reference = [f"Vampb_r_{seq} ampb_r_{seq} 0 1.8" if line.startswith(f"Vampb_r_{seq} ") else line for line in reference]
    if seq == "zz":
        signal_cell = [f"Vamp_s_{seq} amp_s_{seq} 0 0" if line.startswith(f"Vamp_s_{seq} ") else line for line in signal_cell]
        signal_cell = [f"Vampb_s_{seq} ampb_s_{seq} 0 1.8" if line.startswith(f"Vampb_s_{seq} ") else line for line in signal_cell]
    if seq == "zz" or hold_threshold_reference:
        reference = [f"Vamp_r_{seq} amp_r_{seq} 0 0" if line.startswith(f"Vamp_r_{seq} ") else line for line in reference]
        reference = [f"Vampb_r_{seq} ampb_r_{seq} 0 1.8" if line.startswith(f"Vampb_r_{seq} ") else line for line in reference]
    dac_lines=[]
    if threshold_dac_code >= 0:
        reference = [line for line in reference if not line.startswith(f"Vinitlvl_r_{seq} ")]
        dac_output = "thrref" if threshold_drive_mode == "direct" else "thrbuf"
        reference.append(f"Rinitlvl_r_{seq} initlvl_r_{seq} {dac_output} {threshold_drive_r:g}")
        reference = [line.replace("sky130_sc_charge_integrator_held cmem_um", "sky130_sc_charge_integrator_held_ota_vcm_init cmem_um")
                     if line.startswith(f"Xcell_r_{seq} ") else line for line in reference]
        for bit in range(24):
            level=1.8 if (threshold_dac_code >> bit) & 1 else 0.0
            dac_lines.append(f"Vthr_b{bit} b{bit} 0 {level:g}")
        dac_lines += ["Vthr_hi vhi 0 0.95", "Vthr_lo vlo 0 0.9",
                      "Xthr_dac thrref b23 b22 b21 b20 b19 b18 b17 b16 b15 b14 b13 b12 b11 b10 b9 b8 b7 b6 b5 b4 b3 b2 b1 b0 vhi vlo vdd 0 r2r_dac_u24"]
        if threshold_drive_mode == "buffered":
            dac_lines += ["Vbnthr vbnn_thr 0 0.65", "Vbpthr vbpp_thr 0 0.75",
                          "Vthr_pre thr_pre 0 PWL(0 1.8 0.099u 1.8 0.100u 1.8 0.101u 0 5.005m 0)",
                          "Vthr_preb thr_preb 0 PWL(0 0 0.099u 0 0.100u 0 0.101u 1.8 5.005m 1.8)",
                          "Xthr_pre vcm thrbuf thr_pre thr_preb vdd 0 transmission_gate",
                          f"Xthr_buf thrbuf thrref thrbuf vbnn_thr vbpp_thr vdd 0 sky130_sc_ota win={4*threshold_buffer_scale:g} wn3={2*threshold_buffer_scale:g} wp3={27.8*threshold_buffer_scale:g} cc=100f",
                          "Rthr_buf thrbuf vcm 1Meg"]
        if initial_precharge_us > 0:
            pre_end = initial_precharge_us
            pre_pwl = f"PWL(0 1.8 {max(pre_end-0.001,0):g}u 1.8 {pre_end:g}u 0 5.005m 0)"
            preb_pwl = f"PWL(0 0 {max(pre_end-0.001,0):g}u 0 {pre_end:g}u 1.8 5.005m 1.8)"
            dac_lines += [f"Vstate_pre state_pre 0 {pre_pwl}", f"Vstate_preb state_preb 0 {preb_pwl}",
                          f"Xstate_presig vcm out_s_{seq} state_pre state_preb vdd 0 transmission_gate",
                          f"Xstate_preref vcm out_r_{seq} state_pre state_preb vdd 0 transmission_gate"]
    elif threshold_uv:
        threshold_state = 0.90 + threshold_uv*1e-6
        reference = [line.replace("0.9", f"{threshold_state:.12f}") if line.startswith(f"Vinitlvl_r_{seq} ") else line
                     for line in reference]
        reference = [line.replace(f"v(out_r_{seq})=0.9", f"v(out_r_{seq})={threshold_state:.12f}") if line.startswith(".ic ") else line
                     for line in reference]
    if passive_packet:
        for cell_lines in (signal_cell, reference):
            for index, line in enumerate(cell_lines):
                if not line.startswith("Xcell_"):
                    continue
                if "sky130_sc_charge_integrator_held_ota_vcm_init" in line:
                    cell_lines[index] = line.replace("sky130_sc_charge_integrator_held_ota_vcm_init", "sky130_sc_charge_integrator_passive_dac_init")
                elif "sky130_sc_charge_integrator_held " in line:
                    cell_lines[index] = line.replace("sky130_sc_charge_integrator_held ", "sky130_sc_charge_integrator_passive ")
                else:
                    raise ValueError("passive packet mode cannot map this cell topology")
        def mask_inactive_packet_slots(cell_lines: list[str], name: str, active_sequence: str) -> None:
            for index,line in enumerate(cell_lines):
                source=None
                if line.startswith(f"Vconn_{name} "): source="connect"
                elif line.startswith(f"Vconnb_{name} "): source="connect_b"
                elif line.startswith(f"VpacketReset_{name} "): source="packet_reset"
                elif line.startswith(f"VpacketResetb_{name} "): source="packet_reset_b"
                elif line.startswith(f"Vamp_{name} "): source="amp"
                elif line.startswith(f"Vampb_{name} "): source="amp_b"
                if source is None: continue
                match=re.search(r"PWL\((.*)\)",line)
                if not match: continue
                points=match.group(1).split()
                for slot,symbol in enumerate(active_sequence):
                    if symbol != "z": continue
                    first=5+slot*8
                    points[first]=f"{(0 if source in ('connect','packet_reset','amp') else 1.8):g}"
                    points[first+2]=points[first]
                cell_lines[index]=line[:match.start(1)]+" ".join(points)+line[match.end(1):]
        mask_inactive_packet_slots(signal_cell,f"s_{seq}",seq)
        mask_inactive_packet_slots(reference,f"r_{seq}",seq)
    if stacked_packet_isolation:
        if not passive_packet:
            raise ValueError("stacked packet isolation requires --passive-packet")
        for cell_lines in (signal_cell, reference):
            for index,line in enumerate(cell_lines):
                if line.startswith("Xcell_") and "sky130_sc_charge_integrator_passive " in line:
                    cell_lines[index]=line.replace("sky130_sc_charge_integrator_passive ","sky130_sc_charge_integrator_passive_stack2 ")
        lines += [
            ".subckt sky130_sc_charge_integrator_passive_stack2 out sum packet_top packet_bottom reset reset_b packet_reset packet_reset_b init_level init init_b connect connect_b amp_enable amp_enable_b vbiasn vbiasp vdd vss vcm params: cmem_um=100 cpacket_um=1",
            "Xcfb out sum membrane_mim w_um={cmem_um} l_um={cmem_um}",
            "Rdc out sum 1e15",
            "Xpacket packet_top packet_bottom membrane_mim w_um={cpacket_um} l_um={cpacket_um}",
            "Xpacket_connect_a packet_bottom packet_mid connect connect_b vdd vss transmission_gate",
            "Xpacket_connect_b packet_mid out connect connect_b vdd vss transmission_gate",
            "Xpacket_reset packet_bottom vcm packet_reset packet_reset_b vdd vss transmission_gate",
            "Xsum_hold sum vcm vdd vss vdd vss transmission_gate",
            "Xstate_reset out vcm reset reset_b vdd vss transmission_gate",
            "Xstate_init out init_level init init_b vdd vss transmission_gate",
            "Xsum_init sum vcm init init_b vdd vss transmission_gate",
            ".ends sky130_sc_charge_integrator_passive_stack2",
        ]
    if stacked_hold_isolation:
        if not passive_packet or stacked_packet_isolation:
            raise ValueError("stacked hold isolation requires passive mode and cannot be combined with stacked packet isolation")
        for cell_lines in (signal_cell, reference):
            for index,line in enumerate(cell_lines):
                if line.startswith("Xcell_") and "sky130_sc_charge_integrator_passive " in line:
                    cell_lines[index]=line.replace("sky130_sc_charge_integrator_passive ","sky130_sc_charge_integrator_passive_holdstack2 ")
        lines += [
            ".subckt sky130_sc_charge_integrator_passive_holdstack2 out sum packet_top packet_bottom reset reset_b packet_reset packet_reset_b init_level init init_b connect connect_b amp_enable amp_enable_b vbiasn vbiasp vdd vss vcm params: cmem_um=100 cpacket_um=1",
            "Xcfb out sum membrane_mim w_um={cmem_um} l_um={cmem_um}",
            "Rdc out sum 1e15",
            "Xpacket packet_top packet_bottom membrane_mim w_um={cpacket_um} l_um={cpacket_um}",
            "Xpacket_connect packet_bottom out connect connect_b vdd vss transmission_gate",
            "Xpacket_reset packet_bottom vcm packet_reset packet_reset_b vdd vss transmission_gate",
            "Xsum_hold sum vcm vdd vss vdd vss transmission_gate",
            "Xstate_reset_a out reset_mid reset reset_b vdd vss transmission_gate",
            "Xstate_reset_b reset_mid vcm reset reset_b vdd vss transmission_gate",
            "Xstate_init_a out init_mid init init_b vdd vss transmission_gate",
            "Xstate_init_b init_mid init_level init init_b vdd vss transmission_gate",
            "Xsum_init sum vcm init init_b vdd vss transmission_gate",
            ".ends sky130_sc_charge_integrator_passive_holdstack2",
        ]
    if differential_packet:
        def add_balanced_packet(cell_lines: list[str], name: str) -> list[str]:
            packet_line = next(line for line in cell_lines if line.startswith(f"Vpkt_{name} "))
            match = re.search(r"PWL\((.*)\)", packet_line)
            if not match:
                raise ValueError("packet source is not a PWL waveform")
            points = match.group(1).split()
            for point in range(1, len(points), 2):
                points[point] = f"{1.8 - float(points[point]):.12g}"
            cell_lines.append(f"Vpktb_{name} ptopb_{name} 0 PWL(" + " ".join(points) + ")")
            for index, line in enumerate(cell_lines):
                if not line.startswith(f"Xcell_{name} "):
                    continue
                tokens = line.split()
                ptop_index = tokens.index(f"ptop_{name}")
                tokens[ptop_index + 2:ptop_index + 2] = [f"ptopb_{name}", f"pbotb_{name}"]
                subckt_index = next(i for i, token in enumerate(tokens) if token.startswith("sky130_sc_charge_integrator_"))
                original = tokens[subckt_index]
                if original.endswith("_ota_vcm_init"):
                    tokens[subckt_index] = "sky130_sc_charge_integrator_held_diffpacket_ota_vcm_init"
                elif original == "sky130_sc_charge_integrator_held":
                    tokens[subckt_index] = "sky130_sc_charge_integrator_held_diffpacket"
                else:
                    raise ValueError(f"unsupported differential packet cell: {original}")
                cell_lines[index] = " ".join(tokens)
            return cell_lines
        signal_cell = add_balanced_packet(signal_cell, f"s_{seq}")
        reference = add_balanced_packet(reference, f"r_{seq}")
    lines += signal_cell
    lines += reference
    lines += dac_lines
    # Isolate membrane nodes from the readout. ABBA phase windows at 4.900-4.904ms.
    lines += [
        f"Vbnro_{seq} vbnn_ro_{seq} 0 PWL(0 0.65 4.8989m 0.65 4.899m 0.65 4.9404m 0.65 4.9405m 0 5.005m 0)",
        f"Vbpro_{seq} vbpp_ro_{seq} 0 PWL(0 0.75 4.8989m 0.75 4.899m 0.75 4.9404m 0.75 4.9405m 1.8 5.005m 1.8)",
        f"VselA_{seq} sela_{seq} 0 PWL(0 1.8 4.9001m 1.8 4.9101m 1.8 4.9102m 0 4.9303m 0 4.9304m 1.8 4.9404m 1.8 4.9405m 0)",
        f"VselAb_{seq} selab_{seq} 0 PWL(0 0 4.9001m 0 4.9101m 0 4.9102m 1.8 4.9303m 1.8 4.9304m 0 4.9404m 0 4.9405m 1.8)",
        f"VselB_{seq} selb_{seq} 0 PWL(0 0 4.9001m 0 4.9101m 1.8 4.9202m 1.8 4.9203m 1.8 4.9303m 1.8 4.9304m 0 4.9404m 0 4.9405m 0)",
        f"VselBb_{seq} selbb_{seq} 0 PWL(0 1.8 4.9001m 1.8 4.9101m 0 4.9202m 0 4.9203m 0 4.9303m 0 4.9304m 1.8 4.9404m 1.8 4.9405m 1.8)",
        f"Xms_{seq} out_s_{seq} gs_{seq} resetb_{seq} reset_{seq} vdd 0 transmission_gate",
        f"Xmr_{seq} out_r_{seq} gr_{seq} resetb_{seq} reset_{seq} vdd 0 transmission_gate",
        f"Xbufs_{seq} buf_s_{seq} gs_{seq} buf_s_{seq} vbnn_ro_{seq} vbpp_ro_{seq} vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
        f"Xbufr_{seq} buf_r_{seq} gr_{seq} buf_r_{seq} vbnn_ro_{seq} vbpp_ro_{seq} vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
        f"Rbufs_{seq} buf_s_{seq} vcm 1Meg", f"Rbufr_{seq} buf_r_{seq} vcm 1Meg",
        f"Xra_{seq} buf_r_{seq} refsel_{seq} sela_{seq} selab_{seq} vdd 0 transmission_gate",
        f"Xrb_{seq} buf_s_{seq} refsel_{seq} selb_{seq} selbb_{seq} vdd 0 transmission_gate",
        f"Xsa_{seq} buf_s_{seq} sigsel_{seq} sela_{seq} selab_{seq} vdd 0 transmission_gate",
        f"Xsb_{seq} buf_r_{seq} sigsel_{seq} selb_{seq} selbb_{seq} vdd 0 transmission_gate",
        f"Xrg_{seq} refsel_{seq} inp_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
        f"Xrf_{seq} out_{seq} inp_{seq} 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={rf_length:g}",
        f"Rload_{seq} out_{seq} vcm 1Meg",
        f"Xamp_{seq} inp_{seq} sigsel_{seq} out_{seq} vbnn_ro_{seq} vbpp_ro_{seq} vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
    ]
    if direct_read_buffer:
        lines = [line for line in lines
                 if not line.startswith(f"Xms_{seq} ") and not line.startswith(f"Xmr_{seq} ")]
        lines = [line.replace(f" gs_{seq} ", f" out_s_{seq} ").replace(f" gr_{seq} ", f" out_r_{seq} ")
                 if line.startswith((f"Xbufs_{seq} ", f"Xbufr_{seq} ")) else line for line in lines]
    if read_buffer_scale != 1:
        lines = [line.replace("win=4 wn3=2 wp3=27.8",
                              f"win={4*read_buffer_scale:g} wn3={2*read_buffer_scale:g} wp3={27.8*read_buffer_scale:g}")
                 if line.startswith((f"Xbufs_{seq} ", f"Xbufr_{seq} ")) else line for line in lines]
    data_name = f"sky130_sc_physical_chopped_readout_{tag}.dat"
    data = RES / data_name
    if init_only:
        if threshold_dac_code < 0:
            raise ValueError("--init-only requires --threshold-dac-code")
        end_us = max(100.0, init_start_us + init_duration_us + 20.0)
        lines += [".option numdgt=15", ".control", "set numdgt=15", "set wr_singlescale", "set wr_vecnames",
                  f"tran {max_step_ns:g}n {end_us:g}u uic",
                  f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(thrref)",
                  "quit", ".endc", ".end"]
    else:
        lines += [".option numdgt=15", ".control", "set numdgt=15", "set wr_singlescale", "set wr_vecnames", f"tran {max_step_ns:g}n 5.005m uic",
                  f"meas tran pre_s find v(out_s_{seq}) at=4.89m", f"meas tran pre_r find v(out_r_{seq}) at=4.89m",
                  f"meas tran a1 find v(out_{seq}) at=4.909m", f"meas tran b1 find v(out_{seq}) at=4.919m",
                  f"meas tran b2 find v(out_{seq}) at=4.929m", f"meas tran a2 find v(out_{seq}) at=4.939m",
                  f"meas tran post_s find v(out_s_{seq}) at=4.95m", f"meas tran post_r find v(out_r_{seq}) at=4.95m",
                  f"meas tran state_a1 find v(out_s_{seq}) at=4.909m", f"meas tran ref_a1 find v(out_r_{seq}) at=4.909m",
                  f"meas tran state_b1 find v(out_s_{seq}) at=4.919m", f"meas tran ref_b1 find v(out_r_{seq}) at=4.919m",
                  f"meas tran state_b2 find v(out_s_{seq}) at=4.929m", f"meas tran ref_b2 find v(out_r_{seq}) at=4.929m",
                  f"meas tran state_a2 find v(out_s_{seq}) at=4.939m", f"meas tran ref_a2 find v(out_r_{seq}) at=4.939m",
              f"wrdata ../results/{data_name} v(out_s_{seq}) v(out_r_{seq}) v(buf_s_{seq}) v(buf_r_{seq}) v(out_{seq})"+
              ((" v(thrref)" + (" v(thrbuf)" if threshold_drive_mode == "buffered" else "")) if threshold_dac_code >= 0 else ""),
                  "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_physical_chopped_readout_{tag}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{ROOT / 'artifacts/analog_asic'}:/workspace/artifacts/analog_asic", "--workdir",
           "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", str(timeout_s), "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s + 15)
    (RES / f"sky130_sc_physical_chopped_readout_{tag}.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    log = run.stdout + run.stderr
    parsed = {k:float(v) for k,v in __import__("re").findall(r"(?im)^\s*([a-z][a-z0-9_]*)\s*=\s*([-+0-9.eE]+)", log)}
    trace = {}
    target_times = {"early":(init_start_us+0.5*init_duration_us)*1e-6,"late":(init_end_us+20.0)*1e-6} if init_only else {"a1":4.909e-3,"b1":4.919e-3,"b2":4.929e-3,"a2":4.939e-3,"pre":4.89e-3,"post":4.95e-3}
    best = {k:float("inf") for k in target_times}
    if data.exists():
        for line in data.read_text(encoding="utf-8").splitlines()[1:]:
            try: row=[float(v) for v in line.split()]
            except ValueError: continue
            for k,t in target_times.items():
                err=abs(row[0]-t)
                if err<best[k]: best[k]=err; trace[k]=row
    report = {"test":"sky130_physical_membrane_abba_chopped_readout","sequence":seq,
              "feedback_resistor_length_um":rf_length,"threshold_reference_offset_uv":threshold_uv,
              "membrane_cap_square_width_um":membrane_cap_um,"packet_cap_square_width_um":packet_cap_um,
              "threshold_dac_code":threshold_dac_code if threshold_dac_code >= 0 else None,"packet_topplate_step_v":packet_step_v,
              "positive_packet_step_v":positive_packet_step_v,"negative_packet_step_v":negative_packet_step_v,
              "early_positive_packet_scale":early_positive_scale,"early_negative_packet_scale":early_negative_scale,
              "early_packet_event_time_us":early_event_us,"late_packet_event_time_us":late_event_us,
              "multi_event_count":multi_event_count if multi_event_count else None,
              "multi_event_polarity":multi_event_polarity if multi_event_count else None,
              "max_transient_step_ns":max_step_ns,"initialization_duration_us":init_duration_us,
              "initial_precharge_duration_us":initial_precharge_us if threshold_dac_code >= 0 else None,
              "positive_weight_packet_polarity_inverted":invert_packet_polarity,
              "differential_balanced_packet":differential_packet,
              "passive_packet_bottom_connected_to_membrane":passive_packet,
              "packet_reset_and_connection_suppressed_for_inactive_slots":passive_packet,
              "series_packet_isolation_switches":2 if stacked_packet_isolation else 1,
              "series_state_reset_and_init_switches":2 if stacked_hold_isolation else 1,
              "read_buffer_permanently_connected_to_membrane":direct_read_buffer,
              "read_buffer_device_scale":read_buffer_scale,
              "bipolar_charge_buckets":bipolar_charge_buckets,
              "bucket_integrator_ota_always_on":bucket_ota_always_on if bipolar_charge_buckets else None,
              "bucket_integrator_ota_always_off":bucket_ota_always_off if bipolar_charge_buckets else None,
              "threshold_reference_held_on_DAC_for_bin":hold_threshold_reference if threshold_dac_code >= 0 else None,
              "threshold_drive_mode":threshold_drive_mode if threshold_dac_code >= 0 else None,
              "threshold_buffer_device_scale":threshold_buffer_scale if threshold_dac_code >= 0 and threshold_drive_mode == "buffered" else None,
              "threshold_buffer_series_resistance_ohm":threshold_drive_r if threshold_dac_code >= 0 and threshold_drive_mode == "buffered" else None,
              "simulation_completed":run.returncode==0 and all(k in trace for k in target_times),"return_code":run.returncode,
              "scope":("5ms physical MIM membrane pair; packet bottom directly connects to stored state, OTA absent during accumulation, ABBA buffered readout; schematic only, no mismatch/noise/extraction" if passive_packet else "5ms physical MIM membrane pair, signed packet integration, unity OTA isolation, ABBA swapped closed-loop readout; schematic only, no mismatch/noise/extraction")}
    if report["simulation_completed"]:
        if init_only:
            report["scope"] = "physical paired SC membrane DAC initialization screen; no ABBA phases or event packets; schematic TT, no mismatch/noise/extraction"
            report.update({"init_only_duration_us":max(100.0, init_start_us+init_duration_us+20.0),
                           "signal_minus_threshold_uv_at_early_sample":(trace["early"][1]-trace["early"][2])*1e6,
                           "signal_minus_threshold_uv_at_late_sample":(trace["late"][1]-trace["late"][2])*1e6,
                           "threshold_dac_uv_at_late_sample":(trace["late"][3]-0.9)*1e6})
            (RES/f"sky130_sc_physical_chopped_readout_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
            print(json.dumps(report,indent=2))
            return 0
        da=(trace["a1"][5]+trace["a2"][5])/2; db=(trace["b1"][5]+trace["b2"][5])/2
        pre=trace["pre"][1]-trace["pre"][2]; post=trace["post"][1]-trace["post"][2]
        phase_state={k:(trace[k][1]-trace[k][2])*1e6 for k in ("a1","b1","b2","a2")}
        phase_buffer={k:(trace[k][3]-trace[k][4])*1e6 for k in ("a1","b1","b2","a2")}
        avg_state=sum(phase_state.values())/4
        avg_buffer=sum(phase_buffer.values())/4
        actual_gain=((da-db)*.5e6/avg_buffer) if avg_buffer else None
        input_equivalent_error=(((da-db)*.5e6/actual_gain)-avg_state) if actual_gain else None
        report.update({"phase_a_outputs_v":[trace["a1"][5],trace["a2"][5]],"phase_b_outputs_v":[trace["b1"][5],trace["b2"][5]],
            "chopped_output_uv":(da-db)*.5e6,"membrane_diff_before_uv":pre*1e6,
            "membrane_diff_each_phase_uv":phase_state,"mean_membrane_diff_during_read_uv":avg_state,
            "buffer_diff_each_phase_uv":phase_buffer,"mean_buffer_diff_during_read_uv":avg_buffer,
            "buffer_vs_membrane_diff_error_uv":avg_buffer-avg_state,
            "actual_closed_loop_gain_from_buffer_diff":actual_gain,
            # Normalize with this run's measured closed-loop gain. A fixed 10.1
            # gain was stale after the ABBA feedback network was changed and
            # falsely inflated the large-signal readout error.
            "chopped_input_equivalent_error_uv":input_equivalent_error,
            "threshold_decision_sign_correct":(((da-db)>0)==(avg_state>0)),
            "membrane_diff_after_uv":post*1e6,"membrane_read_disturbance_uv":(post-pre)*1e6})
        if threshold_dac_code >= 0:
            report["loaded_threshold_dac_output_uv_from_vcm"]={k:(trace[k][6]-0.9)*1e6 for k in ("a1","b1","b2","a2","pre","post")}
            if threshold_drive_mode == "buffered":
                report["loaded_threshold_buffer_output_uv_from_vcm"]={k:(trace[k][7]-0.9)*1e6 for k in ("a1","b1","b2","a2","pre","post")}
    (RES/f"sky130_sc_physical_chopped_readout_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
