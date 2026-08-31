#!/usr/bin/env python3
"""Run the dedicated epoch-35 exported full-DAG cocotb replay."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if shutil.which("iverilog") is None:
        print("BLOCKED: Icarus Verilog is unavailable.")
        return 2
    root = Path(__file__).resolve().parents[1]
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "verification/cocotb/test_exported_replay_runner.py",
        ],
        cwd=root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
