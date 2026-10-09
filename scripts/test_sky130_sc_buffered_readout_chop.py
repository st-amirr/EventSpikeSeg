"""Test two-phase signal/reference swapping on the buffered closed-loop readout."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from characterize_sky130_sensor_vth_mismatch import PDK_MODEL, make_variant

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
DEFAULT_GAIN = 10.1
HEADER = r"""* SKY130 buffered closed-loop readout with signal/reference phase swap
.option scale=1u reltol=1e-6 abstol=1e-15 vntol=1e-9
.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"
.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"
.include "../pdk/sky130_fd_pr/models/parasitics/sky130_fd_pr__model__parasitic__res_po.model.spice"
.param sky130_fd_pr__res_high_po__slope_spectre=0 sky130_fd_pr__res_high_po__con_slope_spectre=0
.param crpf_precision=1.06e-4 crpfsw_precision_1_1=5.04e-11
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po__base.model.spice"
.include "../pdk/sky130_fd_pr/cells/res_xhigh_po/sky130_fd_pr__res_xhigh_po_1p41.model.spice"
.param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38
.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.corner.spice"
.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__tt.corner.spice"
.include "../../../asic/analog/modules.spice"
.include "../../../asic/analog/sky130_sc_charge_integrator.spice"
Vdd vdd 0 1.8
Vcm vcm 0 0.9
"""


def main() -> int:
    args = sys.argv[1:]
    corner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--corner=")), "tt")
    rcorner = next((a.split("=", 1)[1].lower() for a in args if a.startswith("--rescorner=")), "typical")
    temp = float(next((a.split("=", 1)[1] for a in args if a.startswith("--temp-c=")), "27"))
    gain = float(next((a.split("=", 1)[1] for a in args if a.startswith("--gain=")), str(DEFAULT_GAIN)))
    # Va=G*Vs-(G-1)*Vr, Vb=G*Vr-(G-1)*Vs; (Va-Vb)/2=(G-0.5)*(Vs-Vr).
    demod_gain = gain-0.5
    if demod_gain <= 0:
        raise ValueError("nominal noninverting gain must exceed 0.5")
    delta_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--delta-uv=")), "0.145"))
    common_v = float(next((a.split("=", 1)[1] for a in args if a.startswith("--common-mode-v=")), "0.9"))
    rf_length = float(next((a.split("=", 1)[1] for a in args if a.startswith("--rf-length=")), str(338*(gain-1))))
    physical_mim = "--physical-mim" in args
    reduced_mim_series = "--reduced-mim-series" in args
    regenerative_latch = "--regenerative-latch" in args
    pex_sample_cap = "--pex-sample-cap" in args
    shared_input_mux = "--shared-input-mux" in args
    latch_offset_uv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--latch-offset-uv=")), "0"))
    physical_trim_code = next((int(a.split("=", 1)[1]) for a in args if a.startswith("--physical-trim-code=")), None)
    cap_trim_code = next((int(a.split("=", 1)[1]) for a in args if a.startswith("--cap-trim-code=")), None)
    cap_trim_fine_code = next((int(a.split("=", 1)[1]) for a in args if a.startswith("--cap-trim-fine-code=")), None)
    physical_cap_trim_switches = "--physical-cap-trim-switches" in args
    extracted_weighted_cap_array = "--extracted-weighted-cap-array" in args
    coarse_plate_swing_mv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--coarse-plate-swing-mv=")), "2"))
    fine_plate_swing_mv = float(next((a.split("=", 1)[1] for a in args if a.startswith("--fine-plate-swing-mv=")), "0.5"))
    trim_unit_cap_ff = float(next((a.split("=", 1)[1] for a in args if a.startswith("--trim-unit-cap-ff=")), "9.52"))
    latch_trim_current_na = float(next((a.split("=", 1)[1] for a in args if a.startswith("--latch-trim-current-na=")), "0"))
    latch_trim_mos_vg = float(next((a.split("=", 1)[1] for a in args if a.startswith("--latch-trim-mos-vg-v=")), "0"))
    latch_trim_mos_width = float(next((a.split("=", 1)[1] for a in args if a.startswith("--latch-trim-mos-width-um=")), "1"))
    latch_trim_mos_hold_ns = float(next((a.split("=", 1)[1] for a in args if a.startswith("--latch-trim-mos-hold-ns=")), "0"))
    trim_state_res = float(next((a.split("=", 1)[1] for a in args if a.startswith("--trim-state-res-ohm=")), "10000"))
    trim_dac_res = float(next((a.split("=", 1)[1] for a in args if a.startswith("--trim-dac-res-ohm=")), "100"))
    latch_input_vth_1sigma = "--latch-input-vth-1sigma" in args
    latch_input_width = float(next((a.split("=", 1)[1] for a in args if a.startswith("--latch-input-width-um=")), "2"))
    swap_latch_mismatch = "--swap-latch-mismatch" in args
    sample_aperture_us = float(next((a.split("=", 1)[1] for a in args if a.startswith("--sample-aperture-us=")), "1" if pex_sample_cap else "0.1"))
    bin_end_us = float(next((a.split("=", 1)[1] for a in args if a.startswith("--bin-end-us=")), "30"))
    max_step_ns = float(next((a.split("=", 1)[1] for a in args if a.startswith("--max-step-ns=")), "10"))
    chop_dwell_us = float(next((a.split("=", 1)[1] for a in args if a.startswith("--chop-dwell-us=")), "0"))
    if bin_end_us < 30 or max_step_ns <= 0:
        raise ValueError("bin-end-us must be >=30; max-step-ns must be positive")
    if chop_dwell_us < 0:
        raise ValueError("custom chop dwell cannot be negative")
    if chop_dwell_us and (chop_dwell_us < 1 or bin_end_us < 3*chop_dwell_us):
        raise ValueError("custom chop dwell must be >=1us and fit three equal phases in the bin")
    if chop_dwell_us and shared_input_mux:
        raise ValueError("shared-input-mux timing is not yet defined for custom chop dwell")
    if chop_dwell_us and regenerative_latch and chop_dwell_us < max(7, sample_aperture_us+0.6):
        raise ValueError("custom dwell must accommodate sampling and latch evaluation before bin end")
    if pex_sample_cap and not physical_mim:
        raise ValueError("pex-sample-cap requires physical-mim so the extracted MIM macro is included")
    if not regenerative_latch and pex_sample_cap:
        raise ValueError("pex-sample-cap requires regenerative-latch")
    if shared_input_mux and not (physical_mim and regenerative_latch and pex_sample_cap):
        raise ValueError("shared-input-mux requires physical-mim, regenerative-latch and pex-sample-cap")
    if latch_offset_uv and not regenerative_latch:
        raise ValueError("latch-offset-uv requires regenerative-latch")
    if physical_trim_code is not None and not (physical_mim and regenerative_latch and pex_sample_cap):
        raise ValueError("physical-trim-code requires physical-mim, regenerative-latch and pex-sample-cap")
    if physical_trim_code is not None and latch_offset_uv:
        raise ValueError("choose ideal latch-offset-uv or physical-trim-code, not both")
    if (cap_trim_code is not None or cap_trim_fine_code is not None) and not (physical_mim and regenerative_latch and pex_sample_cap):
        raise ValueError("capacitive trim requires physical-mim, regenerative-latch and pex-sample-cap")
    if cap_trim_fine_code is not None and cap_trim_code is None:
        raise ValueError("cap-trim-fine-code requires a coarse cap-trim-code")
    if physical_cap_trim_switches and cap_trim_code is None:
        raise ValueError("physical-cap-trim-switches requires a capacitive trim code")
    if extracted_weighted_cap_array and not (physical_cap_trim_switches and cap_trim_fine_code is not None):
        raise ValueError("extracted-weighted-cap-array requires physical switches and coarse plus fine codes")
    if trim_unit_cap_ff <= 0:
        raise ValueError("trim-unit-cap-ff must be positive")
    if coarse_plate_swing_mv <= 0:
        raise ValueError("coarse-plate-swing-mv must be positive")
    if fine_plate_swing_mv <= 0:
        raise ValueError("fine-plate-swing-mv must be positive")
    if trim_unit_cap_ff != 9.52 and not physical_cap_trim_switches:
        raise ValueError("trim-unit-cap-ff requires physical-cap-trim-switches")
    if (cap_trim_code is not None or cap_trim_fine_code is not None) and (physical_trim_code is not None or latch_offset_uv):
        raise ValueError("choose only one ideal voltage, R-2R or capacitive trim method")
    if any(code is not None and not 0 <= code <= 255 for code in (cap_trim_code, cap_trim_fine_code)):
        raise ValueError("capacitive comparator calibration codes must be unsigned 8-bit values")
    if latch_trim_current_na and (latch_offset_uv or physical_trim_code is not None):
        raise ValueError("choose one latch trim method per run")
    if latch_trim_mos_vg and (latch_offset_uv or physical_trim_code is not None or latch_trim_current_na):
        raise ValueError("choose only one ideal voltage, R-2R, current-source or PDK MOS trim method")
    if latch_trim_current_na and not regenerative_latch:
        raise ValueError("latch-trim-current-na requires regenerative-latch")
    if latch_trim_mos_vg and not regenerative_latch:
        raise ValueError("latch-trim-mos-vg-v requires regenerative-latch")
    if latch_trim_mos_width <= 0:
        raise ValueError("latch-trim-mos-width-um must be positive")
    if latch_trim_mos_hold_ns < 0:
        raise ValueError("latch-trim-mos-hold-ns cannot be negative")
    if physical_trim_code is not None and not 0 <= physical_trim_code <= 0xFFFFFF:
        raise ValueError("physical-trim-code must be an unsigned 24-bit analog calibration code")
    if trim_state_res <= 0 or trim_dac_res <= 0:
        raise ValueError("trim summing resistances must be positive")
    if latch_input_vth_1sigma and not regenerative_latch:
        raise ValueError("latch-input-vth-1sigma requires regenerative-latch")
    if swap_latch_mismatch and not latch_input_vth_1sigma:
        raise ValueError("swap-latch-mismatch requires latch-input-vth-1sigma")
    if latch_input_vth_1sigma and corner != "tt":
        raise ValueError("the deterministic published ±1σ mismatch variants in this screen are TT-only")
    if latch_input_width <= 0:
        raise ValueError("latch-input-width-um must be positive")
    if not 0 < sample_aperture_us <= 2:
        raise ValueError("sample-aperture-us must be >0 and <=2")
    if corner not in ("tt", "ss", "ff") or rcorner not in ("typical", "high", "low"):
        raise ValueError("corner must be tt/ss/ff; rescorner typical/high/low")
    cm_tag = f"_cm{common_v:g}v" if common_v != 0.9 else ""
    rf_tag = f"_rf{rf_length:g}" if rf_length != 338*(gain-1) else ""
    gain_tag = f"_g{gain:g}" if gain != DEFAULT_GAIN else ""
    shift_us = bin_end_us - (3*chop_dwell_us if chop_dwell_us else 30.0)
    mem_init_open_us = 0.5 if (physical_trim_code is not None or cap_trim_code is not None) else 1.0
    sample_precharge_open_us = 1.5 if (physical_trim_code is not None or cap_trim_code is not None) else 1.0
    sample_precharge_slew_us = 0.01 if (physical_trim_code is not None or cap_trim_code is not None) else 0.0001
    offset_tag = f"_loff{latch_offset_uv:g}uv".replace("-", "m").replace(".", "p") if latch_offset_uv else ""
    width_tag = f"_win{latch_input_width:g}u" if latch_input_width != 2 else ""
    trim_tag = f"_trimdac24c{physical_trim_code}" if physical_trim_code is not None else ""
    cap_trim_tag = f"_trimcap8c{cap_trim_code}" if cap_trim_code is not None else ""
    fine_trim_tag = f"_finecap8c{cap_trim_fine_code}" if cap_trim_fine_code is not None else ""
    cap_trim_tg_tag = (f"_trimtgpex_sc{coarse_plate_swing_mv:g}_sf{fine_plate_swing_mv:g}mv"
                       if extracted_weighted_cap_array else "_trimtgpex" if physical_cap_trim_switches else "")
    current_tag = f"_trimcur{latch_trim_current_na:g}na".replace("-", "m").replace(".", "p") if latch_trim_current_na else ""
    mos_tag = f"_trimnmos{latch_trim_mos_vg:g}v_w{latch_trim_mos_width:g}u_h{latch_trim_mos_hold_ns:g}ns".replace("-", "m").replace(".", "p") if latch_trim_mos_vg else ""
    dwell_tag = f"_dwell{chop_dwell_us:g}u" if chop_dwell_us else ""
    tag = f"{corner}_r{rcorner}_t{temp:g}c_d{delta_uv:g}uv{cm_tag}{gain_tag}{rf_tag}" + ("_physicalmim" if physical_mim else "") + ("_reducedmim" if reduced_mim_series else "") + dwell_tag + ("_latch" if regenerative_latch else "") + ("_pexsample" if pex_sample_cap else "") + ("_sharedmux" if shared_input_mux else "") + ("_latchvth1sigma" + ("_swap" if swap_latch_mismatch else "") if latch_input_vth_1sigma else "") + width_tag + offset_tag + trim_tag + cap_trim_tag + fine_trim_tag + cap_trim_tg_tag + current_tag + mos_tag + (f"_bin{bin_end_us:g}u" if bin_end_us != 30 else "")
    tag += "_benchv5"
    mim_model_include = "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"
    lines = [f"SKY130 buffered closed-loop chopped differential readout {tag}", HEADER]
    if reduced_mim_series:
        if not physical_mim:
            raise ValueError("reduced-mim-series requires physical-mim")
        model=(OUT/"pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice").read_text(encoding="ascii")
        model=model.replace("c1 c0       a 'czero' tc1 = 0 tc2 = 0.0\nrs1 a        b1 'r1' tc1 = {tc1rm4} tc2 = {tc2rm4}\nrs2 b1        c1 'r2' tc1 = {tc1rvia4} tc2 = {tc2rvia4}", "c1 c0       c1 'czero' tc1 = 0 tc2 = 0.0")
        (BENCH/"sky130_mim_model_reduced.spice").write_text(model,encoding="ascii")
        if "\nrs1 " in model or "\nrs2 " in model or "c1 c0       c1 'czero'" not in model:
            raise RuntimeError("MIM reduction did not replace the expected series RC")
        mim_model_include = "sky130_mim_model_reduced.spice"
    if physical_cap_trim_switches:
        lines[1] += "\n.option method=gear maxord=2"
    lines[1] = lines[1].replace("Vcm vcm 0 0.9", f"Vcm vcm 0 {common_v:.12f}")
    if rcorner != "typical":
        lines[1] = lines[1].replace("res_typical__cap_typical__lin.spice", f"res_{rcorner}__cap_{rcorner}__lin.spice")
    lines[1] = lines[1].replace("__tt.corner.spice", f"__{corner}.corner.spice")
    if latch_input_vth_1sigma:
        model_source = PDK_MODEL.read_text(encoding="ascii")
        (BENCH / "nfet_vthsigma_plus.spice").write_text(make_variant(model_source, "plus", +1), encoding="ascii")
        (BENCH / "nfet_vthsigma_minus.spice").write_text(make_variant(model_source, "minus", -1), encoding="ascii")
        lines[1] += '\n.include "nfet_vthsigma_plus.spice"\n.include "nfet_vthsigma_minus.spice"'
    if physical_trim_code is not None:
        lines[1] += '\n.include "../../../asic/analog/sky130_ms_r2r24.spice"'
    dv = delta_uv * 1e-6
    if physical_mim:
        lines[1] += f'\n.include "{mim_model_include}"\n.include "../layout/sky130_mim_state_bank_square/mim_state_square_3x4_w30_l30.spice"'
        if extracted_weighted_cap_array:
            lines[1] += '\n.include "../layout/sky130_cap_trim_weighted_array/sky130_cap_trim_weighted_array_pex.spice"'
        if shared_input_mux or physical_cap_trim_switches or cap_trim_code is not None:
            lines[1] += '\n.include "../layout/sky130_transmission_gate/sky130_transmission_gate_pex.spice"\n.subckt sky130_pex_tg a b en enb vdd vss\nXpex a b en enb vdd vss sky130_transmission_gate_raw\n.ends sky130_pex_tg'
        state_src = ["Xstate_sig sigstate vcm mim_state_square_3x4_w30_l30",
                     "Xstate_ref refstate vcm mim_state_square_3x4_w30_l30",
                     f"Rcm_sig sigstate vcm 1e15", f"Rcm_ref refstate vcm 1e15",
                     f"Vmem_init_sig srcsig 0 {common_v+dv:.12f}", f"Vmem_init_ref srcref 0 {common_v:.12f}",
                     f"Vinit_mem init_mem 0 PWL(0 1.8 {mem_init_open_us:g}u 1.8 {mem_init_open_us+0.0001:g}u 0 {bin_end_us:g}u 0)",
                     ".model init_sw sw ron=1 roff=1e30 vt=0.9 vh=0.1",
                     "Sinit_sig sigstate srcsig init_mem 0 init_sw", "Sinit_ref refstate srcref init_mem 0 init_sw"]
        if shared_input_mux:
            state_src += ["Xstate2_sig sigstate2 vcm mim_state_square_3x4_w30_l30",
                          "Xstate2_ref refstate2 vcm mim_state_square_3x4_w30_l30",
                          "Rcm_sig2 sigstate2 vcm 1e15", "Rcm_ref2 refstate2 vcm 1e15",
                          f"Vmem_init_sig2 srcsig2 0 {common_v-dv:.12f}", f"Vmem_init_ref2 srcref2 0 {common_v:.12f}",
                          "Sinit_sig2 sigstate2 srcsig2 init_mem 0 init_sw", "Sinit_ref2 refstate2 srcref2 init_mem 0 init_sw"]
            mux_on, mux_off = shift_us+5.0, shift_us+18.5
            state_src += [f"Vmux_en mux_en 0 PWL(0 0 {mux_on-0.1:g}u 0 {mux_on:g}u 1.8 {mux_off:g}u 1.8 {mux_off+0.1:g}u 0 {bin_end_us:g}u 0)",
                          f"Vmux_enb mux_enb 0 PWL(0 1.8 {mux_on-0.1:g}u 1.8 {mux_on:g}u 0 {mux_off:g}u 0 {mux_off+0.1:g}u 1.8 {bin_end_us:g}u 1.8)",
                          "Vmux2_en mux2_en 0 0", "Vmux2_enb mux2_enb 0 1.8",
                          "Rmux_sig mux_sig vcm 100Meg", "Rmux_ref mux_ref vcm 100Meg",
                          "Xmux_sig1 sigstate mux_sig mux_en mux_enb vdd 0 sky130_pex_tg",
                          "Xmux_ref1 refstate mux_ref mux_en mux_enb vdd 0 sky130_pex_tg",
                          "Xmux_sig2 sigstate2 mux_sig mux2_en mux2_enb vdd 0 sky130_pex_tg",
                          "Xmux_ref2 refstate2 mux_ref mux2_en mux2_enb vdd 0 sky130_pex_tg"]
            sig_input, ref_input = "mux_sig", "mux_ref"
        else:
            sig_input, ref_input = "sigstate", "refstate"
    else:
        state_src = [f"Vsig sigsrc 0 {common_v+dv:.12f}", f"Vref refsrc 0 {common_v:.12f}"]
        sig_input, ref_input = "sigsrc", "refsrc"
    lines += [f".temp {temp:g}", *state_src,
              "Vbn vbnn 0 0.65", "Vbp vbpp 0 0.75",
              f"Xbufs bufs {sig_input} bufs vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
              f"Xbufr bufr {ref_input} bufr vbnn vbpp vdd 0 sky130_sc_ota win=4 wn3=2 wp3=27.8 cc=100f",
              "Rbufs bufs vcm 1Meg", "Rbufr bufr vcm 1Meg",
              (f"VselA sela 0 PWL(0 1.8 {shift_us+chop_dwell_us-0.1:g}u 1.8 {shift_us+chop_dwell_us:g}u 0 {shift_us+2*chop_dwell_us-0.1:g}u 0 {shift_us+2*chop_dwell_us:g}u 1.8 {bin_end_us:g}u 1.8)" if chop_dwell_us else f"VselA sela 0 PWL(0 1.8 {shift_us+10.1:g}u 1.8 {shift_us+10.2:g}u 0 {shift_us+22.1:g}u 0 {shift_us+22.2:g}u 1.8 {shift_us+29.9:g}u 1.8 {bin_end_us:g}u 0)"),
              (f"VselAb selab 0 PWL(0 0 {shift_us+chop_dwell_us-0.1:g}u 0 {shift_us+chop_dwell_us:g}u 1.8 {shift_us+2*chop_dwell_us-0.1:g}u 1.8 {shift_us+2*chop_dwell_us:g}u 0 {bin_end_us:g}u 0)" if chop_dwell_us else f"VselAb selab 0 PWL(0 0 {shift_us+10.1:g}u 0 {shift_us+10.2:g}u 1.8 {shift_us+22.1:g}u 1.8 {shift_us+22.2:g}u 0 {shift_us+29.9:g}u 0 {bin_end_us:g}u 1.8)"),
              (f"VselB selb 0 PWL(0 0 {shift_us+chop_dwell_us-0.1:g}u 0 {shift_us+chop_dwell_us:g}u 1.8 {shift_us+2*chop_dwell_us-0.1:g}u 1.8 {shift_us+2*chop_dwell_us:g}u 0 {bin_end_us:g}u 0)" if chop_dwell_us else f"VselB selb 0 PWL(0 0 {shift_us+10.1:g}u 0 {shift_us+10.2:g}u 1.8 {shift_us+22.1:g}u 1.8 {shift_us+22.2:g}u 0 {shift_us+29.9:g}u 0 {bin_end_us:g}u 1.8)"),
              (f"VselBb selbb 0 PWL(0 1.8 {shift_us+chop_dwell_us-0.1:g}u 1.8 {shift_us+chop_dwell_us:g}u 0 {shift_us+2*chop_dwell_us-0.1:g}u 0 {shift_us+2*chop_dwell_us:g}u 1.8 {bin_end_us:g}u 1.8)" if chop_dwell_us else f"VselBb selbb 0 PWL(0 1.8 {shift_us+10.1:g}u 1.8 {shift_us+10.2:g}u 0 {shift_us+22.1:g}u 0 {shift_us+22.2:g}u 1.8 {shift_us+29.9:g}u 1.8 {bin_end_us:g}u 0)"),
              "Xra bufr refsel sela selab vdd 0 transmission_gate", "Xrb bufs refsel selb selbb vdd 0 transmission_gate",
              "Xsa bufs sigsel sela selab vdd 0 transmission_gate", "Xsb bufr sigsel selb selbb vdd 0 transmission_gate",
              "Xrg refsel inp 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l=338",
              f"Xrf out inp 0 sky130_fd_pr__res_xhigh_po_1p41 w=1.41 l={rf_length:g}",
              "Rload out vcm 1Meg", "Xamp inp sigsel out vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f"]
    if regenerative_latch:
        a_off, b_off = ((shift_us+chop_dwell_us-0.5, shift_us+2*chop_dwell_us-0.5)
                        if chop_dwell_us else (shift_us+9.9, shift_us+18.0))
        a_on, b_on = a_off-sample_aperture_us, b_off-sample_aperture_us
        eval_on = b_off+5.0 if chop_dwell_us else shift_us+19.9
        sample_caps = (["Xsample_cap_a sample_a vcm mim_state_square_3x4_w30_l30",
                        "Xsample_cap_b sample_b vcm mim_state_square_3x4_w30_l30"] if pex_sample_cap else
                       ["Csample_a sample_a vcm 100f", "Csample_b sample_b vcm 100f"])
        latch_input_a, latch_input_b = "sample_a", "sample_b"
        latch_offset_nodes: list[str] = []
        if latch_offset_uv:
            latch_offset_nodes = [f"Vlat_offset_a lat_in_a sample_a {latch_offset_uv*0.5:g}u",
                                  f"Vlat_offset_b lat_in_b sample_b {-latch_offset_uv*0.5:g}u"]
            latch_input_a, latch_input_b = "lat_in_a", "lat_in_b"
        elif physical_trim_code is not None:
            code_n = 0xFFFFFF - physical_trim_code
            lines += ["Vtrim_hi trim_hi 0 0.95", "Vtrim_lo trim_lo 0 0.85"]
            for bit in range(24):
                lines += [f"Vtrim_p{bit} trim_pb{bit} 0 {(physical_trim_code >> bit) & 1}",
                          f"Vtrim_n{bit} trim_nb{bit} 0 {(code_n >> bit) & 1}"]
            pins_p = " ".join(f"trim_pb{bit}" for bit in range(23, -1, -1))
            pins_n = " ".join(f"trim_nb{bit}" for bit in range(23, -1, -1))
            lines += [f"Xtrim_dac_p trim_p {pins_p} trim_hi trim_lo vdd 0 r2r_dac_u24",
                      f"Xtrim_dac_n trim_n {pins_n} trim_hi trim_lo vdd 0 r2r_dac_u24",
                      f"Rtrim_state_a sample_a lat_in_a {trim_state_res:g}",
                      f"Rtrim_dac_a trim_p lat_in_a {trim_dac_res:g}",
                      f"Rtrim_state_b sample_b lat_in_b {trim_state_res:g}",
                      f"Rtrim_dac_b trim_n lat_in_b {trim_dac_res:g}"]
            latch_input_a, latch_input_b = "lat_in_a", "lat_in_b"
        elif cap_trim_code is not None:
            # Coarse and optional fine binary-weighted MIM charge DACs. Each
            # binary weight is represented by parallel minimum legal MIM cells
            # because the SKY130 model's mf parameter does not scale C.
            trim_start = (b_off+1.6 if chop_dwell_us and physical_cap_trim_switches
                          else eval_on - (0.3 if physical_cap_trim_switches else 0.1))
            if physical_cap_trim_switches:
                # Sample onto the MIM array with plates clamped to VCM.
                # Buffer isolation finishes at trim_start-0.09us; release
                # precharge afterward, before selection starts at -0.01us.
                sample_hold_end = trim_start-0.07 if extracted_weighted_cap_array else b_off
                lines += [
                    f"Vtrimcap_pre trimcap_pre 0 PWL(0 1.8 {sample_hold_end:g}u 1.8 {sample_hold_end+0.01:g}u 0 {bin_end_us:g}u 0)",
                    f"Vtrimcap_preb trimcap_preb 0 PWL(0 0 {sample_hold_end:g}u 0 {sample_hold_end+0.01:g}u 1.8 {bin_end_us:g}u 1.8)",
                ]
            if extracted_weighted_cap_array:
                coarse_swing, fine_swing = coarse_plate_swing_mv*1e-3, fine_plate_swing_mv*1e-3
                lines += [f"Vtrimcap_hi trimcap_hi 0 {common_v+coarse_swing/2:.9f}",
                          f"Vtrimcap_lo trimcap_lo 0 {common_v-coarse_swing/2:.9f}",
                          f"Vfinecap_hi finecap_hi 0 {common_v+fine_swing/2:.9f}",
                          f"Vfinecap_lo finecap_lo 0 {common_v-fine_swing/2:.9f}"]
                bank_pins: list[str] = []
                for bank, prefix, side_code, state_node in (
                    ("COARSE_P", "trimcap", cap_trim_code, "sample_a"),
                    ("COARSE_N", "trimcap", 255-cap_trim_code, "sample_b"),
                    ("FINE_P", "finecap", cap_trim_fine_code, "sample_a"),
                    ("FINE_N", "finecap", 255-cap_trim_fine_code, "sample_b"),
                ):
                    assert side_code is not None
                    side = "a" if state_node == "sample_a" else "b"
                    state_node = "lat_in_a" if state_node == "sample_a" else "lat_in_b"
                    for bit in range(8):
                        plate = f"{prefix}_{side}_b{bit}"
                        bank_pins.extend([state_node, plate])
                        en_hi = f"{plate}_hi_en"
                        en_hi_b = f"{plate}_hi_enb"
                        en_lo = f"{plate}_lo_en"
                        en_lo_b = f"{plate}_lo_enb"
                        hi_selected = (side_code >> bit) & 1
                        lines += [
                            f"X{plate}_pre {plate} vcm trimcap_pre trimcap_preb vdd 0 sky130_pex_tg",
                            f"X{plate}_hi {plate} {prefix}_hi {en_hi} {en_hi_b} vdd 0 sky130_pex_tg",
                            f"X{plate}_lo {plate} {prefix}_lo {en_lo} {en_lo_b} vdd 0 sky130_pex_tg",
                        ]
                        for rail, en, enb, selected in (("hi", en_hi, en_hi_b, hi_selected),
                                                        ("lo", en_lo, en_lo_b, not hi_selected)):
                            high = 1.8 if selected else 0.0
                            low = 0.0 if selected else 1.8
                            lines += [f"V{plate}_{rail}_en {en} 0 PWL(0 0 {trim_start-0.01:g}u 0 {trim_start:g}u {high:g} {bin_end_us:g}u {high:g})",
                                      f"V{plate}_{rail}_enb {enb} 0 PWL(0 1.8 {trim_start-0.01:g}u 1.8 {trim_start:g}u {low:g} {bin_end_us:g}u {low:g})"]
                lines.append("Xtrim_array " + " ".join(bank_pins) + " sky130_cap_trim_weighted_array")
            else:
                def add_cap_bank(prefix: str, code: int, swing_v: float) -> None:
                    lo, hi = common_v-swing_v*0.5, common_v+swing_v*0.5
                    if physical_cap_trim_switches:
                        lines.extend([f"V{prefix}_hi {prefix}_hi 0 {hi:.9f}",
                                      f"V{prefix}_lo {prefix}_lo 0 {lo:.9f}"])
                    for side, node, high_units in (("a", "lat_in_a", code),
                                                    ("b", "lat_in_b", 255-code)):
                        for rail, units, level in (("hi", high_units, hi), ("lo", 255-high_units, lo)):
                            if not units:
                                continue
                            plate = f"{prefix}_{side}_{rail}"
                            if physical_cap_trim_switches:
                                lines.append(f"C{prefix}_{side}_{rail} {node} {plate} {trim_unit_cap_ff*1e-15*units:.12g}")
                            else:
                                lines.extend(f"X{prefix}_{side}_{rail}_{unit} {node} {plate} sky130_fd_pr__cap_mim_m3_2 w=2 l=2"
                                             for unit in range(units))
                            if physical_cap_trim_switches:
                                en, enb = f"{prefix}_{side}_{rail}_en", f"{prefix}_{side}_{rail}_enb"
                                lines.extend([f"X{prefix}_pre_{side}_{rail} {plate} vcm trimcap_pre trimcap_preb vdd 0 sky130_pex_tg",
                                              f"X{prefix}_sel_{side}_{rail} {plate} {prefix}_{rail} {en} {enb} vdd 0 sky130_pex_tg",
                                              f"V{prefix}plate_{side}_{rail}_en {en} 0 PWL(0 0 {trim_start-0.01:g}u 0 {trim_start:g}u 1.8 {bin_end_us:g}u 1.8)",
                                              f"V{prefix}plate_{side}_{rail}_enb {enb} 0 PWL(0 1.8 {trim_start-0.01:g}u 1.8 {trim_start:g}u 0 {bin_end_us:g}u 0)"])
                            else:
                                lines.append(f"V{prefix}plate_{side}_{rail} {plate} 0 PWL(0 {common_v:g} {trim_start-0.01:g}u {common_v:g} {trim_start:g}u {level:g} {bin_end_us:g}u {level:g})")
                add_cap_bank("trimcap", cap_trim_code, 0.1)
                if cap_trim_fine_code is not None:
                    add_cap_bank("finecap", cap_trim_fine_code, fine_plate_swing_mv*1e-3)
            if extracted_weighted_cap_array:
                # Isolate the capacitive trim array and regenerative latch from
                # the chopper's sampled-output node. A continuous unity OTA
                # drives each latch/trim node, avoiding a switched-link
                # kickback into the sub-microvolt sample.
                lines += ["Rlat_in_a lat_in_a vcm 1e15", "Rlat_in_b lat_in_b vcm 1e15",
                          "Xlatbuf_a latbuf_a sample_a latbuf_a vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f",
                          "Xlatbuf_b latbuf_b sample_b latbuf_b vbnn vbpp vdd 0 sky130_sc_ota wn3=2 wp3=27.8 cc=100f"]
                buf_connect, buf_disconnect = b_off+0.2, trim_start-0.1
                lines += [f"Vlat_buf_iso_en latbufiso 0 PWL(0 0 {buf_connect-0.01:g}u 0 {buf_connect:g}u 1.8 {buf_disconnect:g}u 1.8 {buf_disconnect+0.01:g}u 0 {bin_end_us:g}u 0)",
                          f"Vlat_buf_iso_enb latbufisob 0 PWL(0 1.8 {buf_connect-0.01:g}u 1.8 {buf_connect:g}u 0 {buf_disconnect:g}u 0 {buf_disconnect+0.01:g}u 1.8 {bin_end_us:g}u 1.8)",
                          "Xlatbuf_iso_a latbuf_a lat_in_a latbufiso latbufisob vdd 0 sky130_pex_tg",
                          "Xlatbuf_iso_b latbuf_b lat_in_b latbufiso latbufisob vdd 0 sky130_pex_tg"]
            else:
                link_on, link_off = b_off+0.2, bin_end_us
                lines += [f"Vlat_link_en latlink 0 PWL(0 0 {link_on-0.01:g}u 0 {link_on:g}u 1.8 {link_off:g}u 1.8)",
                          f"Vlat_link_enb latlinkb 0 PWL(0 1.8 {link_on-0.01:g}u 1.8 {link_on:g}u 0 {link_off:g}u 0)",
                          "Rlat_in_a lat_in_a vcm 1e15", "Rlat_in_b lat_in_b vcm 1e15",
                          "Xlat_link_a sample_a lat_in_a latlink latlinkb vdd 0 sky130_pex_tg",
                          "Xlat_link_b sample_b lat_in_b latlink latlinkb vdd 0 sky130_pex_tg"]
            latch_input_a, latch_input_b = "lat_in_a", "lat_in_b"
        latch_plus_model, latch_minus_model = (("nfet_vthsigma_minus", "nfet_vthsigma_plus") if swap_latch_mismatch else ("nfet_vthsigma_plus", "nfet_vthsigma_minus")) if latch_input_vth_1sigma else ("sky130_fd_pr__nfet_01v8", "sky130_fd_pr__nfet_01v8")
        lines += [*sample_caps,
                  "Rsample_a sample_a vcm 1e15", "Rsample_b sample_b vcm 1e15",
                  f"Vprecharge precharge 0 PWL(0 1.8 {sample_precharge_open_us-sample_precharge_slew_us:g}u 1.8 {sample_precharge_open_us:g}u 0 {bin_end_us:g}u 0)",
                  f"Vprechargeb prechargeb 0 PWL(0 0 {sample_precharge_open_us-sample_precharge_slew_us:g}u 0 {sample_precharge_open_us:g}u 1.8 {bin_end_us:g}u 1.8)",
                  "Xpre_a vcm sample_a precharge prechargeb vdd 0 transmission_gate",
                  "Xpre_b vcm sample_b precharge prechargeb vdd 0 transmission_gate",
                  f"Vsample_a samplea 0 PWL(0 0 {a_on-0.1:g}u 0 {a_on:g}u 1.8 {a_off:g}u 1.8 {a_off+0.1:g}u 0 {bin_end_us:g}u 0)",
                  f"Vsample_ab sampleab 0 PWL(0 1.8 {a_on-0.1:g}u 1.8 {a_on:g}u 0 {a_off:g}u 0 {a_off+0.1:g}u 1.8 {bin_end_us:g}u 1.8)",
                  f"Vsample_b sampleb 0 PWL(0 0 {b_on-0.1:g}u 0 {b_on:g}u 1.8 {b_off:g}u 1.8 {b_off+0.1:g}u 0 {bin_end_us:g}u 0)",
                  f"Vsample_bb samplebb 0 PWL(0 1.8 {b_on-0.1:g}u 1.8 {b_on:g}u 0 {b_off:g}u 0 {b_off+0.1:g}u 1.8 {bin_end_us:g}u 1.8)",
                  "Xsample_gate_a out sample_a samplea sampleab vdd 0 transmission_gate",
                  "Xsample_gate_b out sample_b sampleb samplebb vdd 0 transmission_gate",
                  f"Vlatclk latclk 0 PWL(0 0 {eval_on-0.1:g}u 0 {eval_on:g}u 1.8 {bin_end_us:g}u 1.8)",
                  *latch_offset_nodes,
                  # This cross-coupled latch resolves with inverted output naming;
                  # swap its inputs so latchp-latchn follows positive membrane state.
                  f"Xread_latch {latch_input_b} {latch_input_a} latclk latchp latchn vdd 0 readout_regen",
                  "Clatchp latchp 0 20f", "Clatchn latchn 0 20f",
                  ".subckt readout_regen inp inn clk outp outn vdd vss",
                  "Xpre_p outp clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
                  "Xpre_n outn clk vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
                  "Xlp outp outn vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
                  "Xln outp outn ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
                  "Xrp outn outp vdd vdd sky130_fd_pr__pfet_01v8 w=4 l=0.5",
                  "Xrn outn outp ltail vss sky130_fd_pr__nfet_01v8 w=2 l=0.5",
                  "Xltail ltail clk vss vss sky130_fd_pr__nfet_01v8 w=8 l=0.5",
                  f"Xin_p outp inp tail vss {latch_plus_model} w={latch_input_width:g} l=0.5",
                  f"Xin_n outn inn tail vss {latch_minus_model} w={latch_input_width:g} l=0.5",
                  "Xtail tail clk vss vss sky130_fd_pr__nfet_01v8 w=4 l=1",
                  ".ends readout_regen"]
        if latch_trim_current_na:
            trim_g = abs(latch_trim_current_na) * 1e-9 / 1.8
            trim_node = "latchp" if latch_trim_current_na > 0 else "latchn"
            lines += [f"Gtrim_eval {trim_node} 0 latclk 0 {trim_g:.12g}"]
        elif latch_trim_mos_vg:
            trim_node = "latchp" if latch_trim_mos_vg > 0 else "latchn"
            trim_vg = abs(latch_trim_mos_vg)
            if latch_trim_mos_hold_ns:
                trim_off_us = eval_on + latch_trim_mos_hold_ns * 1e-3
                trim_fall_us = trim_off_us + 0.01
                trim_gate_pwl = f"PWL(0 0 {eval_on-0.01:g}u 0 {eval_on:g}u {trim_vg:g} {trim_off_us:g}u {trim_vg:g} {trim_fall_us:g}u 0 {bin_end_us:g}u 0)"
            else:
                trim_gate_pwl = f"PWL(0 0 {eval_on-0.1:g}u 0 {eval_on:g}u {trim_vg:g} {bin_end_us:g}u {trim_vg:g})"
            lines += [f"Vtrim_gate trim_gate 0 {trim_gate_pwl}",
                      f"Xtrim_eval {trim_node} trim_gate 0 0 sky130_fd_pr__nfet_01v8 w={latch_trim_mos_width:g} l=0.5"]
    dat_name = f"sky130_sc_buffered_readout_chop_{tag}.dat"
    dat = RES / dat_name
    wr_vectors = "v(out) v(bufs) v(bufr) v(refsel) v(sigsel)" + (" v(sigstate) v(refstate)" if physical_mim else "")
    if shared_input_mux:
        wr_vectors += " v(sigstate2) v(refstate2) v(mux_sig) v(mux_ref)"
    if regenerative_latch:
        wr_vectors += " v(sample_a) v(sample_b) v(latchp) v(latchn)"
        if latch_offset_uv or physical_trim_code is not None or cap_trim_code is not None:
            wr_vectors += " v(lat_in_a) v(lat_in_b)"
        if physical_trim_code is not None:
            wr_vectors += " v(trim_p) v(trim_n)"
    if regenerative_latch:
        wr_vectors += " v(latclk)"
    lines += [".control", "set numdgt=15", "set wr_singlescale", "set wr_vecnames", f"tran {max_step_ns:g}n {bin_end_us:g}u uic",
              f"wrdata ../results/{dat_name} {wr_vectors}", "quit", ".endc", ".end"]
    deck = BENCH / f"sky130_sc_buffered_readout_chop_{tag}.cir"
    deck.write_text("\n".join(lines)+"\n", encoding="utf-8")
    dat.unlink(missing_ok=True)
    sim_timeout = 300 if extracted_weighted_cap_array else 60
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro",
           "--volume", f"{OUT}:/workspace/artifacts/analog_asic", "--workdir", "/workspace/artifacts/analog_asic/benches",
           "--entrypoint", "timeout", "eventspikeseg:analog-ngspice36", str(sim_timeout), "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, text=True, capture_output=True, timeout=sim_timeout+15)
    (RES/f"sky130_sc_buffered_readout_chop_{tag}.log").write_text(run.stdout+run.stderr,encoding="utf-8")
    rows=[]
    if dat.exists():
        for line in dat.read_text(encoding="utf-8").splitlines()[1:]:
            try: rows.append([float(x) for x in line.split()])
            except ValueError: continue
    sim_ok = run.returncode == 0 and len(rows) > 10 and "ngspice-36 done" in (run.stdout+run.stderr).lower() and "tran simulation(s) aborted" not in (run.stdout+run.stderr).lower()
    sim_ok = sim_ok and abs(rows[-1][0]-bin_end_us*1e-6) < 1e-12
    report={"test":"sky130_buffered_closedloop_readout_chopper_screen","process_corner":corner,"resistor_corner":rcorner,
            "temperature_c":temp,"front_end_gain":gain,"feedback_resistor_length_um":rf_length,"input_differential_uv":delta_uv,"simulation_completed":sim_ok,
            "custom_equal_chop_phase_dwell_us":chop_dwell_us or None,
            "diagnostic_mim_series_reduced_to_nominal_capacitance":reduced_mim_series,
            "bench_revision":5,"mim_model_include":mim_model_include if physical_mim else None,
            "ideal_demodulated_gain":demod_gain,
            "return_code":run.returncode,"scope":("physical extracted SKY130 MIM banks to VCM with source-switch initialization and 1PΩ DC returns; OTA buffers" + (" connect through two-state extracted transmission-gate mux" if shared_input_mux else " attach directly") + "; chopper OTA/resistors and sampling transmission gates schematic" + ((" with extracted MIM sample capacitors and schematic regenerative latch" if pex_sample_cap else " with ideal 100f sample capacitors and schematic regenerative latch") if regenerative_latch else "; no latch") + ("; deterministic input-pair mismatch" if latch_input_vth_1sigma else "") + ("; ideal differential gate-offset sources" if latch_offset_uv else "") + ("; nominal MIM capacitance with internal sub-fs series RC reduced" if reduced_mim_series else "") + "; no transient noise/yield" if physical_mim else "amp-only transient; physical unity OTA buffers and xhigh-poly closed-loop readout; same OTA reads normal and swapped inputs; no membrane, comparator latch, mismatch/noise/extraction"),
            "bin_end_us":bin_end_us,"max_transient_step_ns":max_step_ns}
    report["sample_capacitor"] = "extracted 30um-square 12-unit MIM bank (~21.84pF each)" if pex_sample_cap else ("ideal 100fF each" if regenerative_latch else None)
    report["sample_aperture_us"] = sample_aperture_us if regenerative_latch else None
    report["applied_latch_differential_offset_uv"] = latch_offset_uv if regenerative_latch else None
    report["latch_trim_implementation"] = "ideal differential voltage sources at latch gate pins; calibration hardware not implemented" if latch_offset_uv else None
    report["latch_trim_current_na"] = latch_trim_current_na if regenerative_latch else None
    report["latch_trim_current_scope"] = "ideal clock-gated differential output current probe; physical current-mirror implementation not included" if latch_trim_current_na else None
    report["latch_trim_nmos_gate_v"] = latch_trim_mos_vg if regenerative_latch else None
    report["latch_trim_nmos_width_um"] = latch_trim_mos_width if regenerative_latch and latch_trim_mos_vg else None
    report["latch_trim_nmos_hold_ns"] = latch_trim_mos_hold_ns if regenerative_latch and latch_trim_mos_vg else None
    report["latch_trim_nmos_scope"] = "PDK NFET output-current trim, clock-gated by analog gate-bias ramp; no physical trim-bias generator/layout or mismatch on trim device" if latch_trim_mos_vg else None
    report["physical_trim_dac_code24"] = physical_trim_code
    report["physical_trim_dac_scope"] = "PDK-switched complementary analog trim DAC with ideal R-2R elements; code is a calibration control, not a model weight/state quantizer" if physical_trim_code is not None else None
    report["trim_state_resistance_ohm"] = trim_state_res if physical_trim_code is not None else None
    report["trim_dac_resistance_ohm"] = trim_dac_res if physical_trim_code is not None else None
    report["capacitive_trim_code8"] = cap_trim_code
    report["capacitive_trim_fine_code8"] = cap_trim_fine_code
    report["capacitive_trim_scope"] = (("routed 1020-device 8-bit coarse/fine differential MIM array with extracted plate/state interconnect capacitances and 96 PEX TGs in the bench; TGs/decoder are schematic-connected, no switch-array GDS, mismatch/noise or calibration search; comparator calibration only, not model weight/state quantization" if extracted_weighted_cap_array else f"8-bit binary-weighted coarse/fine bank represented by code-summed capacitors at{trim_unit_cap_ff:g}fF/unit, extracted TG plate selectors and VCM precharge; extracted-unit transfer equivalent only, no legal weighted unit-cell tiling, decoder, distributed array parasitics, MIM variation, mismatch/noise, or code search; comparator calibration only, not model weight/state quantization" if physical_cap_trim_switches else "eight-bit binary-weighted pair(s) of minimum 2x2um SKY130 MIM capacitors with ideal plate-voltage controls; comparator offset only, not model weight/state quantization; no plate switch/decoder, noise or trim-array layout") if cap_trim_code is not None else None)
    report["capacitive_trim_unit_cap_f"] = trim_unit_cap_ff*1e-15 if cap_trim_code is not None else None
    report["capacitive_trim_sample_cap_f"] = 21.84e-12 if cap_trim_code is not None else None
    report["capacitive_trim_fine_plate_swing_v"] = fine_plate_swing_mv*1e-3 if cap_trim_fine_code is not None else None
    report["capacitive_trim_coarse_plate_swing_v"] = coarse_plate_swing_mv*1e-3 if extracted_weighted_cap_array else None
    if extracted_weighted_cap_array:
        report["scope"] = report["scope"].replace(
            "OTA buffers attach directly",
            "OTA followers connect through PEX isolation TGs to the latch/trim nodes",
        )
    report["latch_input_vth_mismatch"] = ({"realization_sigma": [-1, +1] if swap_latch_mismatch else [+1, -1],
                                           "source": "SKY130 nfet_01v8 mismatch.corner.spice published vth0 slope; deterministic pair, TT only"}
                                          if latch_input_vth_1sigma else None)
    report["latch_input_width_um"] = latch_input_width if regenerative_latch else None
    if report["simulation_completed"]:
        at=lambda t:min(range(len(rows)),key=lambda i:abs(rows[i][0]-t))
        sample_times = ((0.5*chop_dwell_us, 1.5*chop_dwell_us-0.01,
                         1.5*chop_dwell_us+0.01, 2.5*chop_dwell_us)
                        if chop_dwell_us else (10.0,16.0,22.0,28.0))
        a1,b1,b2,a2=(rows[at((shift_us+t)*1e-6)] for t in sample_times)
        out_a=(a1[1]+a2[1])*.5; out_b=(b1[1]+b2[1])*.5
        chopped=(out_a-out_b)*.5
        expected=demod_gain*delta_uv*1e-6
        report.update({"phase_a_outputs_v":[a1[1],a2[1]],"phase_b_outputs_v":[b1[1],b2[1]],"chopped_output_uv":chopped*1e6,
                       "expected_chopped_output_uv":expected*1e6,"input_equivalent_chopped_error_uv":(chopped-expected)/demod_gain*1e6,
                       "phase_a_buffer_diff_uv":[(a1[2]-a1[3])*1e6] if shared_input_mux else [(a1[2]-a1[3])*1e6,(a2[2]-a2[3])*1e6],
                       "phase_b_buffer_diff_uv":[(b1[2]-b1[3])*1e6] if shared_input_mux else [(b1[2]-b1[3])*1e6,(b2[2]-b2[3])*1e6],
                       "input_delta_sign_correct":(chopped>0)==(delta_uv>0)})
        if physical_mim:
            at_state = lambda t: min(range(len(rows)), key=lambda i: abs(rows[i][0]-t))
            initial = rows[at_state(2e-6)]
            before_t, after_t = ((shift_us+4.9, shift_us+18.8) if shared_input_mux else
                                 (shift_us+(chop_dwell_us-0.6 if chop_dwell_us else 9.9), shift_us+2.5*chop_dwell_us if chop_dwell_us else shift_us+29.0))
            before, after = rows[at_state(before_t*1e-6)], rows[at_state(after_t*1e-6)]
            initial_diff = (initial[6]-initial[7])*1e6
            diff_before = (before[6]-before[7])*1e6
            diff_after = (after[6]-after[7])*1e6
            report.update({"state_diff_after_init_uv":initial_diff,"state_diff_before_readout_uv":diff_before,
                           "state_diff_after_readout_uv":diff_after,
                           "state_disturbance_during_readout_uv":diff_after-diff_before})
            if shared_input_mux:
                decoy_before = (before[8]-before[9])*1e6
                decoy_after = (after[8]-after[9])*1e6
                report.update({"unselected_state_diff_before_readout_uv":decoy_before,
                               "unselected_state_diff_after_readout_uv":decoy_after,
                               "unselected_state_disturbance_uv":decoy_after-decoy_before,
                               "mux_connect_us":shift_us+5.0,"mux_disconnect_us":shift_us+18.6})
        if regenerative_latch:
            lat = rows[at((eval_on+1.1)*1e-6)]
            sampled = rows[at((b_off+0.15)*1e-6)]
            # Additional vectors follow the 5 baseline channels and optional state nodes.
            sample_offset = 1 + 5 + (2 if physical_mim else 0) + (4 if shared_input_mux else 0)
            sample_diff = (sampled[sample_offset]-sampled[sample_offset+1])*1e6
            latch_diff = lat[sample_offset+2]-lat[sample_offset+3]
            report.update({"sampled_phase_difference_uv":sample_diff,"latch_output_difference_v":latch_diff,
                           "latch_decision_sign_correct":(latch_diff>0)==(delta_uv>0),
                           "latch_sample_time_us":eval_on+1.1})
            if latch_offset_uv or physical_trim_code is not None or cap_trim_code is not None:
                input_offset = 1 + 5 + (2 if physical_mim else 0) + (4 if shared_input_mux else 0) + 4
                pre_eval = next(row for row in reversed(rows) if row[0] <= (eval_on-0.11)*1e-6)
                report["pre_eval_measurement_time_us"] = pre_eval[0]*1e6
                report["pre_eval_clock_v"] = pre_eval[-1]
                if abs(pre_eval[-1]) > 1e-12:
                    raise RuntimeError("pre-evaluation measurement overlaps the latch clock ramp")
                actual_input_diff = (pre_eval[input_offset]-pre_eval[input_offset+1])*1e6
                report["effective_latch_gate_difference_uv_pre_eval"] = actual_input_diff
                report["measured_gate_offset_from_sample_diff_uv"] = actual_input_diff - sample_diff
                if physical_trim_code is not None:
                    trim_values = pre_eval
                    report["measured_trim_dac_output_difference_uv"] = (trim_values[input_offset+2]-trim_values[input_offset+3])*1e6
                if cap_trim_code is not None or cap_trim_fine_code is not None:
                    report["measured_capacitive_trim_difference_uv"] = actual_input_diff - sample_diff
            if shared_input_mux:
                sample_a_v, sample_b_v = sampled[sample_offset], sampled[sample_offset+1]
                mux_chopped_uv = (sample_a_v-sample_b_v)*0.5*1e6
                expected_mux_uv = demod_gain*delta_uv
                report.update({"sampled_phase_a_v":sample_a_v,"sampled_phase_b_v":sample_b_v,
                               "phase_a_outputs_v":[sample_a_v],"phase_b_outputs_v":[sample_b_v],
                               "chopped_output_uv":mux_chopped_uv,"expected_chopped_output_uv":expected_mux_uv,
                               "input_equivalent_chopped_error_uv":mux_chopped_uv/demod_gain-delta_uv,
                               "input_delta_sign_correct":(mux_chopped_uv>0)==(delta_uv>0)})
    (RES/f"sky130_sc_buffered_readout_chop_{tag}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["simulation_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
