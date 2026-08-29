#!/usr/bin/env python3
"""Compile and replay reduced-geometry real-checkpoint goldens in Icarus."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

from cocotb.runner import get_runner

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "replay_dir",
        type=Path,
        default=Path("artifacts/asic_rtl_replay_v4_6class"),
        nargs="?",
    )
    parser.add_argument("--residual-capacity", type=int, default=8192)
    parser.add_argument("--timeout-cycles", type=int, default=2_000_000)
    args = parser.parse_args()
    replay_dir = args.replay_dir.resolve()
    generated_top = replay_dir / "eventspikeseg140k_replay_top.sv"
    if not generated_top.is_file():
        raise FileNotFoundError(
            f"{generated_top} is missing; run scripts/prepare_asic_rtl_replay.py first"
        )
    sources = sorted((ROOT / "asic/rtl").glob("*.sv"))
    environment = {
        **os.environ,
        "ASIC_REPLAY_DIR": str(replay_dir),
        "ASIC_REPLAY_TIMEOUT_CYCLES": str(args.timeout_cycles),
        "PYTHONPATH": os.pathsep.join(
            filter(
                None,
                [
                    str(ROOT / "verification/cocotb"),
                    os.environ.get("PYTHONPATH", ""),
                ],
            )
        ),
    }
    with tempfile.TemporaryDirectory(prefix="eventspikeseg-rtl-replay-") as build_dir:
        shutil.copytree(replay_dir / "weights", Path(build_dir) / "weights")
        shutil.copy2(
            ROOT / "verification/cocotb/test_generated_dag_golden.py",
            Path(build_dir) / "test_generated_dag_golden.py",
        )
        runner = get_runner("icarus")
        runner.build(
            verilog_sources=[*sources, generated_top],
            hdl_toplevel="eventspikeseg140k_dag_top",
            build_dir=build_dir,
            always=True,
            build_args=["-g2012"],
            parameters={"RESIDUAL_MAX_EVENTS": args.residual_capacity},
        )
        runner.test(
            hdl_toplevel="eventspikeseg140k_dag_top",
            test_module="test_generated_dag_golden",
            test_dir=build_dir,
            extra_env=environment,
        )


if __name__ == "__main__":
    main()
