"""Prepare and launch the existing full25 categorical graph's physical implementation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/analog_asic"
NAME = "gf180_analog_full25_event_graph_interconnect_v1"
VARIANT = "full25_graph_v1"
CONTAINER = "ess-gf180-full25-graph-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    directory = ROOT / "asic/analog/orfs/gf180_full25_event_graph_v1"
    statuspath = BASE / "assembly/full25_event_graph_layout_v1/status.json"
    assert not statuspath.exists(), "Inspect the recorded job; do not restart it."
    state = subprocess.run(["docker", "inspect", CONTAINER], capture_output=True, text=True)
    assert state.returncode != 0, "Container exists; inspect its authoritative state before reuse."
    source = ROOT / "asic/analog" / (NAME + ".sv")
    text = source.read_text()
    # Preserve bit layout while expressing the actor buses as one packed dimension
    # for the synthesis frontend used by the existing ORFS image.
    text = text.replace("[24:0][31:0]", "[799:0]").replace("[24:0][23:0]", "[599:0]")
    count = 0
    for kind, width in (("payload", 32), ("bin_tag", 24)):
        pattern = r"(actor_(?:in|out)_" + kind + r"_[io])\[(\d+)\]"
        text, n = re.subn(pattern, lambda m: f"{m[1]}[{int(m[2]) * width} +: {width}]", text)
        count += n
    assert count > 0 and not re.search(r"actor_(?:in|out)_(?:payload|bin_tag)_[io]\[(?!\d+ \+:)", text)
    directory.mkdir(parents=True, exist_ok=True)
    flat = directory / "full25_event_graph_flat.sv"
    flat.write_text(text, encoding="utf8")
    relative_sources = [
        "asic/rtl/event_fork2.sv", "asic/rtl/event_join2.sv",
        "asic/rtl/event_upsample2x.sv", "asic/rtl/event_channel_offset.sv",
        "asic/analog/gf180_analog_event_fork2.sv",
        "asic/analog/gf180_analog_event_join2.sv",
        "asic/analog/gf180_analog_event_upsample2x.sv",
        "asic/analog/gf180_analog_binary_event_merge_sorted2.sv",
        "asic/analog/gf180_analog_binary_event_merge_sorted2_wrapper.sv",
        flat.relative_to(ROOT).as_posix(),
    ]
    assert all((ROOT / p).is_file() for p in relative_sources)
    sdc = directory / "constraint.sdc"
    sdc.write_text("create_clock -name clk -period 20.0 [get_ports clk]\nset_clock_uncertainty -setup 1.0 [get_clocks clk]\nset_clock_uncertainty -hold 0.2 [get_clocks clk]\nset_input_delay -max 1.0 -clock clk [all_inputs -no_clocks]\nset_output_delay 1.0 -clock clk [all_outputs]\nset_false_path -from [get_ports reset]\n")
    config = directory / "config.mk"
    config.write_text(f"export DESIGN_NAME = {NAME}\nexport DESIGN_NICKNAME = {NAME}\nexport PLATFORM = gf180\nexport VERILOG_FILES = " + " ".join("/workspace/" + p for p in relative_sources) + f"\nexport SDC_FILE = /workspace/{sdc.relative_to(ROOT).as_posix()}\nexport CORE_UTILIZATION = 30\nexport PLACE_DENSITY = 0.30\nexport CLOCK_PERIOD = 20.0\nexport SYNTH_HIERARCHICAL = 0\nexport ABC_AREA = 1\nexport NUM_CORES = 2\nexport SKIP_CTS_REPAIR_TIMING = 1\n")
    statuspath.parent.mkdir(parents=True, exist_ok=True)
    command = ["docker", "run", "--detach", "--name", CONTAINER, "--network", "none", "--memory", "8g", "--memory-swap", "8g", "--cpus", "2", "--volume", f"{ROOT}:/workspace:ro"]
    for name in ("logs", "objects", "reports", "results"):
        path = BASE / "orfs" / name
        path.mkdir(parents=True, exist_ok=True)
        command += ["--volume", f"{path}:/OpenROAD-flow-scripts/flow/{name}"]
    makeargs = f"DESIGN_CONFIG=/workspace/{config.relative_to(ROOT).as_posix()} FLOW_VARIANT={VARIANT}"
    shell = f"make -C /OpenROAD-flow-scripts/flow {makeargs} && make -C /OpenROAD-flow-scripts/flow {makeargs} do-generate_abstract"
    command += ["--entrypoint", "timeout", "eventspikeseg:orfs-guarded", "3600", "bash", "-lc", shell]
    launch = subprocess.run(command, capture_output=True, text=True)
    assert launch.returncode == 0, launch.stderr
    container_id = launch.stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{64}", container_id)
    data = {"stage": "physical_layout_running", "started_utc": datetime.now(timezone.utc).isoformat(), "container": CONTAINER, "container_id": container_id, "design": NAME, "variant": VARIANT, "purpose": "Physical implementation of all53 categorical event edges and25 actor interfaces, for integration into the full original-float analog assembly.", "analog_scope": "Only spike addresses, tags and control are digital; weights/state/PLIF remain analog.", "packed_bus_conversion_count": count, "command": command, "sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in [source, flat, sdc, config, *[ROOT / p for p in relative_sources[:-1]]]}, "full_chip_layout_complete": False, "behavior_optimization_deferred": True}
    statuspath.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"container": CONTAINER, "container_id": container_id, "status": str(statuspath), "packed_bus_conversion_count": count}, indent=2))


if __name__ == "__main__":
    main()
