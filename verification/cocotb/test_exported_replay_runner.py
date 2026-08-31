from __future__ import annotations

import os
from pathlib import Path

from cocotb.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]
REPLAY = ROOT / "artifacts/RTL/smoke"


def test_exported_epoch35_replay(tmp_path: Path) -> None:
    if not (REPLAY / "eventspikeseg140k_replay_top.sv").is_file():
        raise FileNotFoundError(
            "generate the epoch-35 replay with scripts/prepare_asic_replay.py first"
        )
    sources = sorted((ROOT / "asic/rtl").glob("*.sv"))
    sources.append(REPLAY / "eventspikeseg140k_replay_top.sv")
    runner = get_runner("icarus")
    runner.build(
        verilog_sources=sources,
        hdl_toplevel="eventspikeseg140k_replay_top",
        build_dir=tmp_path / "exported_replay",
        always=True,
        build_args=["-g2012"],
        parameters={"RESIDUAL_MAX_EVENTS": 2048},
    )
    environment = dict(os.environ)
    environment["EVENTSPIKESEG_REPLAY_DIR"] = str(REPLAY)
    runner.test(
        hdl_toplevel="eventspikeseg140k_replay_top",
        test_module="test_exported_dag_replay",
        test_dir=tmp_path / "exported_replay",
        extra_env=environment,
    )
