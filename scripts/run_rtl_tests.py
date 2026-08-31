"""Run native SystemVerilog RTL tests when Icarus Verilog is available."""

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if shutil.which("iverilog") is None:
        print("BLOCKED: Icarus Verilog is unavailable. Install the 'iverilog' package.")
        return 2
    root = Path(__file__).resolve().parents[1]
    return subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "verification/cocotb/test_rtl_runner.py"],
        cwd=root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
