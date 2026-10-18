"""Feed a measured GF180 analog SPIKE sample through the routed page/scatter RTL."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cosim_gf180_neuron_spike_to_page128_v1 import measured_spikes

BASE = ROOT / "artifacts/analog_asic"
BENCH = BASE / "benches/gf180_neuron_page_scatter_cosim_v1_tb.sv"
TB_GEN = BASE / "benches/gf180_neuron_page_scatter_cosim_v1_generated_tb.sv"
LOG = BASE / "benches/gf180_neuron_page_scatter_cosim_v1.log"
REPORT = BASE / "results/gf180_neuron_page_scatter_cosim_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    voltages = measured_spikes()
    cmos_vih = 0.7 * 3.3
    bitmap = 1 if voltages["high"] >= cmos_vih else 0
    if bitmap != 1:
        raise RuntimeError(f"Measured high-arm SPIKE was not CMOS-high: {voltages}")
    tb = BENCH.read_text(encoding="ascii")
    tb = tb.replace("logic [127:0] spike_bitmap_i=128'b1;",
                    f"logic [127:0] spike_bitmap_i=128'h{bitmap:032x};")
    TB_GEN.write_text(tb, encoding="ascii")

    sources = [
        "gf180_analog_binary_event_merge_sorted2.sv",
        "gf180_analog_spike_event_serializer32_v1.sv",
        "gf180_analog_spike_event_page128_v1.sv",
        "gf180_analog_weight_event_scatter_parallel.sv",
        "gf180_analog_weight_event_scatter_pw128.sv",
        "gf180_analog_page_to_pw128_scatter_v1.sv",
    ]
    compile_run = " && ".join([
        "apt-get update -qq && apt-get install -y -qq iverilog >/dev/null",
        "iverilog -g2012 -s gf180_neuron_page_scatter_cosim_v1_tb "
        "-o /workspace/artifacts/analog_asic/benches/gf180_neuron_page_scatter_cosim_v1_tb.vvp "
        + " ".join(f"/workspace/asic/analog/{name}" for name in sources)
        + " /workspace/artifacts/analog_asic/benches/gf180_neuron_page_scatter_cosim_v1_generated_tb.sv",
        "vvp /workspace/artifacts/analog_asic/benches/gf180_neuron_page_scatter_cosim_v1_tb.vvp",
    ])
    run = subprocess.run([
        "docker", "run", "--rm", "--network", "bridge", "--memory", "2g", "--cpus", "2",
        "--volume", f"{ROOT}:/workspace", "--workdir", "/workspace",
        "--entrypoint", "bash", "eventspikeseg:analog-ngspice47", "-lc", compile_run,
    ], capture_output=True, text=True, timeout=240)
    log = run.stdout + run.stderr
    LOG.write_text(log, encoding="utf-8")
    passed = run.returncode == 0 and "gf180_neuron_page_scatter_cosim_v1_tb PASS" in log
    analog_report = json.loads((BASE / "results/gf180_neuron_spike_to_page128_v1.json").read_text())
    page_phys = BASE / "assembly/gf180_neuron_page_scatter_link_v1/qualification.json"
    report = {
        "design": "gf180_neuron_page_scatter_cosim_v1",
        "status": "PASS" if passed else "FAIL",
        "scope": "A sample measured at the analog neuron SPIKE terminal is classified at the CMOS VIH boundary, inserted as lane 0 of the channel-parallel page, decoded into a spatial/channel tuple, and accepted by the 128-output analog-weight selector.",
        "analog_sample": {
            "sample_time_us": analog_report["sample_time_us"],
            "spike_voltage_v": voltages["high"],
            "cmos_vih_v": cmos_vih,
            "classified_high": bool(bitmap),
        },
        "page_event": {"pixel_index": 821, "pixel_xy": [21, 10], "channel": 0,
                       "bin_tag_hex": "abc123", "multiplicity": 1},
        "expected_pointwise_selector": {"output_channel_base": 0, "input_channel_local": 0,
                                         "tap": 0, "output_xy": [21, 10]},
        "physical_parent": "artifacts/analog_asic/assembly/gf180_neuron_page_scatter_link_v1/qualification.json",
        "physical_full_style_flat_drc_count": json.loads(page_phys.read_text())["magic_full_style_flat_drc_count"],
        "limitations": [
            "The selected analog weight values and injected charge remain outside this event-selector simulation.",
            "Only the neuron-to-lane0 physical connection is included; lanes 1-127 are interface pins.",
            "The full 43-node graph, whole-model accuracy, loaded analog RC, and 5 ms full-population service remain open."
        ],
        "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in
                   [Path(__file__), BENCH, TB_GEN, LOG, page_phys,
                    BASE / "results/gf180_five_module_parent_nominal_srcf6f1e759f510.dat",
                    *(ROOT / "asic/analog" / name for name in sources)]},
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
