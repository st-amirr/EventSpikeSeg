"""Compare extracted SKY130 diode forward I-V with an ordinary SPICE control diode."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "artifacts/analog_asic/benches"
RESULTS = ROOT / "artifacts/analog_asic/results"
DIODE = ROOT / "artifacts/analog_asic/layout/sky130_diode_pd2nw_05v5_probe_1x1/diode_pd2nw_05v5_probe_pex.spice"
QUAL = DIODE.parent / "qualification.json"
STEM = "sky130_diode_forward_iv_tt27_extracted_vs_control"


def main() -> None:
    version = "47" if "--ngspice47" in sys.argv[1:] else "36"
    stem = f"{STEM}_ngspice47" if version == "47" else STEM
    qual = json.loads(QUAL.read_text(encoding="utf-8"))
    if not (qual["magic_drc_zero"] and qual["netgen_lvs_unique_match"]
            and qual["ports_in_extracted_order"] == ["ANODE", "SUB", "CATHODE"]):
        raise RuntimeError("diode physical qualification/terminal order failed")
    deck = BENCH / f"{stem}.cir"
    deck.write_text("\n".join([
        "* Extracted SKY130 diode and ordinary SPICE forward I-V control",
        '.lib "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice/sky130.lib.spice" tt',
        f'.include "/workspace/{DIODE.relative_to(ROOT).as_posix()}"',
        ".temp 27", "Vd a 0 0", "Xdiode a 0 0 diode_pd2nw_05v5_probe",
        "Ectrl b 0 a 0 1", "Dctrl b 0 control_diode",
        ".model control_diode d(is=1e-15 n=1.36)",
        ".control", "set numdgt=15", "dc Vd 0 3 0.5", "print i(Vd) i(Ectrl)",
        "quit", ".endc", ".end", "",
    ]), encoding="ascii")
    cmd = ["docker", "run", "--rm", "--memory", "4g", "--cpus", "2",
           "--volume", f"{ROOT}:/workspace", "--workdir",
           "/workspace/artifacts/analog_asic/pdk/ciel_root/sky130A/libs.tech/ngspice",
           "--entrypoint", "timeout", f"eventspikeseg:analog-ngspice{version}", "120", "ngspice", "-b",
           f"/workspace/{deck.relative_to(ROOT).as_posix()}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=135, cwd=ROOT)
    log = proc.stdout + proc.stderr
    log_path = RESULTS / f"{stem}.log"
    log_path.write_text(log, encoding="utf-8")
    rows = [{"forward_v": float(v), "pdk_extracted_current_a": abs(float(pdk)),
             "ordinary_control_current_a": abs(float(ctrl))}
            for _, v, pdk, ctrl in re.findall(
                r"(?m)^(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)", log)]
    complete = proc.returncode == 0 and f"ngspice-{version} done" in log and len(rows) == 7
    report = {
        "test": f"sky130_extracted_diode_forward_iv_ngspice{version}",
        "simulation_completed": complete, "return_code": proc.returncode,
        "physical_diode_qualification": str(QUAL.relative_to(ROOT)).replace("\\", "/"),
        "ordinary_control_model": "D(is=1e-15 A, n=1.36); simulator sanity control only, not a substitute PDK model",
        "rows": rows,
        "source_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (DIODE, QUAL, deck, log_path)},
        "decision": "Compare simulator versions and require a physically addressed signed write before accepting the diode state.",
        "limitations": "DC model diagnostic at TT/27C. The ordinary control diode is intentionally generic and has no process meaning. No physical write driver, charge pump, word/bit selection, half-select disturb, event-precision update, PVT/noise/mismatch or array service. PDK model warnings about unrecognized parameters are retained in the log.",
    }
    out = RESULTS / f"{stem}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "simulation_completed": complete,
                      "rows": rows, "error_tail": log[-1200:] if not complete else None}, indent=2))
    if not complete:
        raise RuntimeError(f"incomplete diode I-V screen: {log[-1200:]}")


if __name__ == "__main__":
    main()
