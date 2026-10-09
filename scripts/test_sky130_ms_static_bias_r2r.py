"""Characterize a shared R-2R bias ladder loaded by physical injector gates.

The R-2R is the existing ideal 1k/2k resistor network with PDK MOS switches.
This test does not quantize learned weights: it generates only five shared bias
voltages; each branch retains the same fixed geometry and event waveform.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/analog_asic"
BENCH = OUT / "benches"
RES = OUT / "results"
BITS = 8
VMAX = (1 << BITS) - 1


def main() -> int:
    global BITS, VMAX
    BENCH.mkdir(parents=True, exist_ok=True)
    RES.mkdir(parents=True, exist_ok=True)
    BITS = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                    if arg.startswith("--dac-bits=")), "8"))
    if not 4 <= BITS <= 16:
        raise ValueError("shared bias DAC screen supports 4-16 bits")
    VMAX = (1 << BITS) - 1
    stem = "sky130_ms_static_bias_r2r" + (f"_b{BITS}" if BITS != 8 else "")
    event_trim = "--trim-event-from-first" in sys.argv[1:] or "--trim-event-reverse" in sys.argv[1:]
    reverse_event_trim = "--trim-event-reverse" in sys.argv[1:]
    all_biases = "--all-biases" in sys.argv[1:]
    event_mode = "--event-transfer" in sys.argv[1:] or event_trim
    # Nominal shared bias values correspond to the five previously screened
    # gate fractions. P/N commands follow the established physical injector.
    bias_arg = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--biases=")), None)
    fractions = (tuple(float(v) for v in bias_arg.split(",")) if bias_arg else
                 ((0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95) if all_biases else (0.5, 0.8))) if event_mode else (
                     tuple(float(v) for v in bias_arg.split(",")) if bias_arg else (0.4, 0.5, 0.6, 0.7, 0.8))
    allowed_fractions = (0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)
    if any(f not in allowed_fractions for f in fractions) or len(set(fractions)) != len(fractions):
        raise ValueError("bias fractions must be unique members of 0.4,0.5,0.6,0.7,0.8,0.85,0.9,0.95")
    geom_arg = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--geometry-scale=")), None)
    geometry_override = float(geom_arg) if geom_arg else None
    corner = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                   if arg.startswith("--mos-corner=")), "tt")
    temp_c = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                         if arg.startswith("--temperature-c=")), "27"))
    polarity = next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                     if arg.startswith("--polarity=")), "positive")
    if polarity not in ("positive", "negative"):
        raise ValueError("polarity must be positive or negative")
    gate_slew_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                              if arg.startswith("--gate-slew-ns=")), "0.1"))
    clamp_slew_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                if arg.startswith("--clamp-slew-ns=")), "0.1"))
    event_count = int(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                            if arg.startswith("--event-count=")), "1"))
    event_spacing_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                   if arg.startswith("--event-spacing-ns=")), "50"))
    event_width_ns = float(next((arg.split("=", 1)[1] for arg in sys.argv[1:]
                                 if arg.startswith("--event-width-ns=")), "10.5"))
    trim = "--trim-from-nominal" in sys.argv[1:]
    reuse_trim = "--reuse-tt-trim" in sys.argv[1:] or event_mode
    if event_trim:
        reuse_trim = True
    if corner not in ("tt", "ss", "ff") or trim and reuse_trim:
        raise ValueError("choose one MOS corner and at most one trim mode")
    if gate_slew_ns <= 0:
        raise ValueError("gate slew must be positive")
    if clamp_slew_ns <= 0:
        raise ValueError("clamp release slew must be positive")
    if event_width_ns <= 0 or event_count < 1 or event_spacing_ns <= event_width_ns + gate_slew_ns:
        raise ValueError("event count must be positive and spacing must exceed pulse width plus gate slew")
    prior = None
    base_trim = None
    if trim or reuse_trim:
        bias_suffix = ("_biases" + "-".join(v.replace(".", "p") for v in bias_arg.split(","))) if bias_arg else ""
        prior_name = (f"{stem}_event_tt_temp27_reuse_tt_trim.json" if event_trim else
                      f"{stem}{bias_suffix}_trimmed.json" if reuse_trim and bias_arg else
                      f"{stem}_trimmed.json" if reuse_trim else
                      f"{stem}.json")
        if reuse_trim and bias_arg and not (RES / prior_name).exists():
            prior_name = f"{stem}_trimmed.json"
        prior = json.loads((RES / prior_name).read_text(encoding="utf-8"))
        if reuse_trim and not event_trim:
            # A custom rail may be present in a separately trimmed group
            # (for example, 0.85/0.90/0.95). Select a report that actually
            # contains every requested P/N rail rather than silently falling
            # back to the nominal five-rail report.
            candidates = [prior]
            for path in sorted(RES.glob(f"{stem}_biases*_trimmed.json")):
                candidate = json.loads(path.read_text(encoding="utf-8"))
                if candidate.get("simulation_completed"):
                    candidates.append(candidate)
            required = {(fraction, pol) for fraction in fractions for pol in ("p", "n")}
            matching = next((candidate for candidate in candidates
                             if required.issubset({(row["gate_fraction"], row["polarity"])
                                                   for row in candidate.get("rows", [])})), None)
            if matching is None:
                raise RuntimeError(f"no TT-trimmed rail report contains all requested biases: {fractions}")
            prior = matching
        if not prior.get("simulation_completed"):
            raise RuntimeError("nominal R-2R gate-load report is missing or incomplete")
        trim_path = (RES / (f"{stem}{bias_suffix}_trimmed.json" if bias_arg else f"{stem}_trimmed.json"))
        base_trim = (json.loads(trim_path.read_text(encoding="utf-8"))
                     if event_trim else prior)
    rails: dict[str, tuple[float, int, int]] = {}
    for i, fraction in enumerate(fractions):
        for pol, target in (("p", 1.8 - fraction * 1.08), ("n", fraction * 0.6)):
            nominal = round(target / 1.8 * VMAX)
            code = nominal
            if trim:
                prior_row = next((row for row in prior["rows"]
                                  if row["gate_fraction"] == fraction and row["polarity"] == pol), None)
                # One ideal LSB is used only as a starting estimate. The
                # second PDK run verifies the resulting physically loaded code.
                code = round(nominal + ((target - prior_row["loaded_dac_v"]) / (1.8 / VMAX)
                                        if prior_row is not None else 0))
                code = min(VMAX, max(0, code))
            elif reuse_trim:
                prior_row = next(row for row in base_trim["rows"]
                                 if row["gate_fraction"] == fraction and row["polarity"] == pol)
                code = prior_row["trimmed_dac_code"]
            if event_trim:
                event_row = next(row for row in prior["event_transfer_rows"]
                                 if row["gate_fraction"] == fraction)
                # Test one paired code step from the prior event error. The
                # direction is deliberately selectable because P/N effects
                # on signed differential charge are coupled and nonlinear.
                step = 1 if event_row["relative_event_error"] > 0 else -1
                code += -step if reverse_event_trim else step
                code = min(VMAX, max(0, code))
            rails[f"{pol}{i}"] = (target, code, nominal)

    lines = [
        "SKY130 shared static gate bias R2R gate-load comparison",
        ".option scale=1u reltol=1e-5 abstol=1e-15 vntol=1e-9",
        f".temp {temp_c:g}",
        '.include "../pdk/sky130_fd_pr/models/parameters/invariant.spice"',
        '.include "../pdk/sky130_fd_pr/models/r+c/res_typical__cap_typical__lin.spice"',
        ".param m4_dw=0 tol_m4=0 tc1rm4=0 tc2rm4=0 tc1rvia4=0 tc2rvia4=0 rm4=0.047 rcvia4=0.38",
        f'.include "../pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{corner}.corner.spice"',
        f'.include "../pdk/sky130_fd_pr/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{corner}.corner.spice"',
        '.include "../pdk/sky130_fd_pr/cells/cap_mim_m3/sky130_fd_pr__cap_mim_m3_2.model.spice"',
        "Vdd vdd 0 1.8", "Vcm vcm 0 0.9",
        ".subckt bias_dac_tg a b en enb vdd vss",
        "Xn a en b vss sky130_fd_pr__nfet_01v8 w=1 l=0.15 m=100",
        "Xp a enb b vdd sky130_fd_pr__pfet_01v8 w=2 l=0.15 m=100",
        ".ends bias_dac_tg",
    ]
    if event_mode:
        stop_us = 3.0 + (event_count - 1) * event_spacing_ns / 1000 + event_width_ns / 1000 + gate_slew_ns / 1000 + 0.06
        after_us = 3.0 + (event_count - 1) * event_spacing_ns / 1000 + event_width_ns / 1000 + 0.02
        clamp_end = 2.99 + clamp_slew_ns / 1000
        select_points = [(0.0, 0.0)]
        for event_index in range(event_count):
            start = 3.0 + event_index * event_spacing_ns / 1000
            select_points.extend(((start, 0.0), (start + gate_slew_ns / 1000, 1.8),
                                  (start + event_width_ns / 1000, 1.8),
                                  (start + event_width_ns / 1000 + gate_slew_ns / 1000, 0.0)))
        select_points.append((stop_us, 0.0))
        def pwl(points: list[tuple[float, float]]) -> str:
            return "PWL(" + " ".join(f"{time:.9g}u {value:g}" for time, value in points) + ")"
        select = pwl(select_points)
        select_b = pwl([(t, 1.8 - v) for t, v in select_points])
        lines += [
            '.include "../../../asic/analog/modules.spice"',
            '.include "../../../asic/analog/sky130_ms_plif.spice"',
            ".subckt diff_inject vp vn pp nn vdd vss params: geom=1",
            "Xp_pos vp pp vdd vdd sky130_fd_pr__pfet_01v8 w={1.5*geom} l=10",
            "Xn_neg vn nn vss vss sky130_fd_pr__nfet_01v8 w={geom} l=10",
            ".ends diff_inject",
            f"Vcl cl 0 PWL(0 1.8 2.99u 1.8 {clamp_end:.9g}u 0 {stop_us:.9g}u 0)",
            f"Vclb clb 0 PWL(0 0 2.99u 0 {clamp_end:.9g}u 1.8 {stop_us:.9g}u 1.8)",
            f"Vsel sel 0 {select}",
            f"Vselb selb 0 {select_b}",
            f"Vidle idle 0 {select_b}",
            f"Vidleb idleb 0 {select}",
        ]

    # This bounded 8-bit shared-bias DAC keeps the same passive R-2R topology
    # and PDK transmission-gate switching, without replicating the existing
    # experimental 24-bit ladder's very large high-drive buffers.
    for rail, (target, code, nominal) in rails.items():
        for k in range(BITS):
            lines.append(f"V{rail}_b{k} {rail}_b{k} 0 {1.8 if ((code >> k) & 1) else 0:g}")
            lines.append(f"V{rail}_bb{k} {rail}_bb{k} 0 {0 if ((code >> k) & 1) else 1.8:g}")
        lines += [f"R{rail}_term {rail}_n0 0 2k",
                  f"R{rail}_q{BITS-1} {rail}_out {rail}_n{BITS-2} 1k"]
        for k in range(BITS-2, 0, -1):
            lines.append(f"R{rail}_q{k} {rail}_n{k} {rail}_n{k-1} 1k")
        for k in range(BITS-1, -1, -1):
            node = f"{rail}_out" if k == BITS-1 else f"{rail}_n{k}"
            lines += [f"R{rail}_2b{k} {node} {rail}_m{k} 2k",
                      f"X{rail}_hi{k} vdd {rail}_m{k} {rail}_b{k} {rail}_bb{k} vdd 0 bias_dac_tg",
                      f"X{rail}_lo{k} 0 {rail}_m{k} {rail}_bb{k} {rail}_b{k} vdd 0 bias_dac_tg"]
        # Static mode tests one gate load. Event mode loads the DAC through
        # physical injector gates only during the presynaptic pulse.
        if not event_mode:
            if rail.startswith("p"):
                lines.append(f"Xload_{rail} {rail}_out vdd vdd vdd sky130_fd_pr__pfet_01v8 w=6 l=10")
            else:
                lines.append(f"Xload_{rail} {rail}_out 0 0 0 sky130_fd_pr__nfet_01v8 w=4 l=10")
        lines.append(f"R{rail}_dc {rail}_out 0 1G")

    if event_mode:
        for i, fraction in enumerate(fractions):
            geom = geometry_override if geometry_override is not None else (4 if all_biases or fraction == 0.5 else 2)
            for source in ("dac", "ideal"):
                for event in (False, True):
                    name = f"f{i}_{source}_{'event' if event else 'zero'}"
                    lines += [
                        f"Xmem_p_{name} vp_{name} vcm membrane_mim w_um=10 l_um=10",
                        f"Xmem_n_{name} vn_{name} vcm membrane_mim w_um=10 l_um=10",
                        f"Xcl_p_{name} vcm vp_{name} cl clb vdd 0 transmission_gate",
                        f"Xcl_n_{name} vcm vn_{name} cl clb vdd 0 transmission_gate",
                    ]
                    for pol, idle_v in (("p", "1.8"), ("n", "0")):
                        rail = f"{pol}{i}"
                        bias_node = f"{rail}_out"
                        if source == "ideal":
                            ideal_node = f"{rail}_ideal"
                            if not event:
                                lines.append(f"V{rail}_ideal {ideal_node} 0 {rails[rail][0]:.12g}")
                            bias_node = ideal_node
                        gate = f"{pol}g_{name}"
                        idle_node = f"{gate}_idle"
                        lines += [
                            f"V{idle_node} {idle_node} 0 {idle_v}",
                            f"X{gate}_bias {bias_node} {gate} {'sel' if event else '0'} {'selb' if event else 'vdd'} vdd 0 transmission_gate",
                            f"X{gate}_idle {idle_node} {gate} {'idle' if event else 'vdd'} {'idleb' if event else '0'} vdd 0 transmission_gate",
                        ]
                    state_p, state_n = ((f"vp_{name}", f"vn_{name}") if polarity == "positive" else
                                        (f"vn_{name}", f"vp_{name}"))
                    lines.append(f"Xinj_{name} {state_p} {state_n} pg_{name} ng_{name} vdd 0 diff_inject params: geom={geom}")

    lines += [".control", "set numdgt=15"]
    if event_mode:
        lines.append(f"tran 0.25n {stop_us:.9g}u uic")
        for i in range(len(fractions)):
            for source in ("dac", "ideal"):
                for case in ("zero", "event"):
                    name = f"f{i}_{source}_{case}"
                    lines += [f"let d_{name}=v(vp_{name})-v(vn_{name})",
                              f"meas tran before_{name} find d_{name} at=2.998u",
                              f"meas tran after_{name} find d_{name} at={after_us:.9g}u"]
    else:
        lines.append("op")
        for rail in rails:
            lines.append(f"print v({rail}_out)")
    lines += ["quit", ".endc", ".end"]
    slew_tag = "" if gate_slew_ns == 0.1 else f"_slew{gate_slew_ns:g}n".replace(".", "p")
    clamp_tag = "" if clamp_slew_ns == 0.1 else f"_clamp{clamp_slew_ns:g}n".replace(".", "p")
    event_trim_tag = "_event_trimmed_reverse" if reverse_event_trim else "_event_trimmed"
    bias_tag = ("_biases" + "-".join(v.replace(".", "p") for v in bias_arg.split(","))) if bias_arg else ""
    geom_tag = f"_geom{geometry_override:g}".replace(".", "p") if event_mode and geometry_override is not None else ""
    polarity_tag = "_neg" if event_mode and polarity == "negative" else ""
    train_tag = f"_n{event_count}_p{event_spacing_ns:g}n" if event_mode and event_count > 1 else ""
    width_tag = f"_w{event_width_ns:g}n".replace(".", "p") if event_mode and event_width_ns != 10.5 else ""
    suffix = (event_trim_tag if event_trim else "_event_all5" if event_mode and all_biases else "_event" if event_mode else "") + bias_tag + geom_tag + slew_tag + clamp_tag + polarity_tag + ("_trimmed" if trim else
              f"_{corner}_temp{temp_c:g}_reuse_tt_trim" if reuse_trim else
              ("" if corner == "tt" and temp_c == 27 else
               f"_{corner}_temp{temp_c:g}".replace(".", "p"))) + width_tag + train_tag
    deck = BENCH / f"{stem}{suffix}.cir"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["docker", "run", "--rm", "--memory", "8g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace:ro", "--volume", f"{OUT}:/workspace/artifacts/analog_asic",
           "--workdir", "/workspace/artifacts/analog_asic/benches", "--entrypoint", "timeout",
           "eventspikeseg:analog-ngspice36", "120", "ngspice", "-b", deck.name]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=135)
    log = run.stdout + run.stderr
    (RES / f"{stem}{suffix}.log").write_text(log, encoding="utf-8")
    measured = {rail: float(value) for rail, value in re.findall(
        r"(?im)^\s*v\((p\d|n\d)_out\)\s*=\s*([-+0-9.eE]+)", log)}
    event_measured = {f"{phase}_{name}": float(value) for phase, name, value in re.findall(
        r"(?im)^\s*(before|after)_(f\d+_(?:dac|ideal)_(?:zero|event))\s*=\s*([-+0-9.eE]+)", log)}
    rows = []
    event_rows = []
    complete = (run.returncode == 0 and
                (len(event_measured) == len(fractions) * 8 if event_mode else len(measured) == len(rails)))
    if complete and not event_mode:
        for i, fraction in enumerate(fractions):
            for pol in ("p", "n"):
                rail = f"{pol}{i}"
                target, code, nominal = rails[rail]
                actual = measured[rail]
                rows.append({"gate_fraction": fraction, "polarity": pol,
                             "target_v": target, "nominal_dac_code": nominal,
                             "trimmed_dac_code": code,
                             "loaded_dac_v": actual,
                             "error_mv": (actual - target) * 1e3,
                             "relative_error": (actual - target) / target if target else None})
    elif complete:
        for i, fraction in enumerate(fractions):
            deltas = {}
            geom = geometry_override if geometry_override is not None else (4 if all_biases or fraction == 0.5 else 2)
            for source in ("dac", "ideal"):
                de = ((event_measured[f"after_f{i}_{source}_event"] - event_measured[f"before_f{i}_{source}_event"]) -
                      (event_measured[f"after_f{i}_{source}_zero"] - event_measured[f"before_f{i}_{source}_zero"]))
                deltas[source] = de
            event_rows.append({"gate_fraction": fraction,
                               "injector_geometry_scale": geom,
                               "ideal_event_delta_uv": deltas["ideal"] * 1e6,
                               "r2r_event_delta_uv": deltas["dac"] * 1e6,
                               "event_delta_error_uv": (deltas["dac"] - deltas["ideal"]) * 1e6,
                               "relative_event_error": (deltas["dac"] - deltas["ideal"]) / deltas["ideal"] if deltas["ideal"] else None})
    report = {
        "test": "sky130_static_shared_gate_bias_r2r_event_transfer" if event_mode else "sky130_static_shared_gate_bias_r2r_mos_gate_load",
        "simulation_completed": complete, "return_code": run.returncode,
        "mos_corner": corner, "temperature_c": temp_c,
        "event_polarity": polarity if event_mode else None,
        "mos_gate_load": "physical PDK injector gate per output during event pulse" if event_mode else "one tied-source/drain PDK injector gate per output",
        "calibration_mode": ("one-code event-charge calibration attempt failed convergence" if event_trim and not complete else
                             ("reverse-direction" if reverse_event_trim else "same-direction") + " paired-rail one-code event-charge adjustment; verified by physical transient" if event_trim else
                             "nominal code mapping" if not trim and not reuse_trim else
                             "one lookup-code correction derived from nominal loaded gate voltage; verified by a second PDK operating-point simulation" if trim else
                             "reuse TT-trimmed codes without recalibration"),
        "r2r_bits": BITS,
        "event_width_ns": event_width_ns if event_mode else None,
        "event_count": event_count if event_mode else None,
        "event_spacing_ns": event_spacing_ns if event_mode else None,
        "gate_selection_slew_ns": gate_slew_ns if event_mode else None,
        "clamp_release_slew_ns": clamp_slew_ns if event_mode else None,
        "r2r_resistors": "ideal 1k/2k; PDK transmission-gate switches; no mismatch/extraction",
        "rows": rows,
        "event_transfer_rows": event_rows,
        "failure_summary": (("bounded Docker/ngspice run exceeded120s" if run.returncode == 124 else
                             "ngspice transient aborted with timestep collapse during switched-gate event calibration")
                            if event_mode and not complete else None),
        "scope": (f"{len(fractions)} shared biases, TT-trimmed {BITS}-bit R-2R driven through physical PDK TGs into physical MOS injector gates and 10um MIM state pairs; ideal-gate branches are matched references. Matched no-event cases are subtracted. No resistor mismatch, noise, extracted RC, full PLIF, threshold/reset or full-float task replay." if event_mode else
                  f"Five shared bias voltage targets only; no learned weight quantization. Bounded {BITS}-bit ideal 1k/2k resistor ladder with PDK transmission-gate switches drives one physical PDK MOS gate per output. This DC load check does not include event transient, full ladder area/power, resistor mismatch, noise, PVT, reference calibration loop, membrane/readout, threshold/reset or full-float closed-loop task accuracy."),
    }
    (RES / f"{stem}{suffix}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
