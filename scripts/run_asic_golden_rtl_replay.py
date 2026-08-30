#!/usr/bin/env python3
"""Compile and replay reduced-geometry real-checkpoint goldens in Icarus."""

from __future__ import annotations

import argparse
import os
import shutil
import xml.etree.ElementTree as ET
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
    parser.add_argument("--simulator", choices=("icarus", "verilator"), default="verilator")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument(
        "--build-dir",
        type=Path,
        help="persistent simulator build directory (default: <replay>/.sim_<simulator>)",
    )
    parser.add_argument("--clean-build", action="store_true")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="run an existing persistent simulator executable without elaboration",
    )
    args = parser.parse_args()
    if args.jobs < 1:
        raise ValueError("jobs must be positive")
    # The replay executable is a verification artifact, so C++ optimization
    # only inflates build time. Command-line make assignments override the
    # Verilator makefile's default -Os for both fast and slow translation units.
    os.environ["MAKEFLAGS"] = f"-j{args.jobs} OPT_FAST=-O0 OPT_SLOW=-O0"
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
    build_dir = (args.build_dir or replay_dir / f".sim_{args.simulator}").resolve()
    if args.clean_build and build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(replay_dir / "weights", build_dir / "weights", dirs_exist_ok=True)
    shutil.copy2(
        ROOT / "verification/cocotb/test_generated_dag_golden.py",
        build_dir / "test_generated_dag_golden.py",
    )
    runner = get_runner(args.simulator)
    build_args = ["-g2012"] if args.simulator == "icarus" else ["--Wno-fatal"]
    if not args.skip_build:
        runner.build(
            verilog_sources=[*sources, generated_top],
            hdl_toplevel="eventspikeseg140k_dag_top",
            build_dir=build_dir,
            always=args.clean_build,
            build_args=build_args,
            parameters={"RESIDUAL_MAX_EVENTS": args.residual_capacity},
        )
    elif not (build_dir / "eventspikeseg140k_dag_top").is_file():
        raise FileNotFoundError("--skip-build requested but simulator executable is absent")
    runner.test(
        hdl_toplevel="eventspikeseg140k_dag_top",
        hdl_toplevel_lang="verilog",
        test_module="test_generated_dag_golden",
        build_dir=build_dir,
        test_dir=build_dir,
        extra_env=environment,
    )
    results = ET.parse(build_dir / "results.xml")
    if results.findall(".//failure"):
        raise SystemExit("cocotb RTL replay failed; see results.xml")


if __name__ == "__main__":
    main()
