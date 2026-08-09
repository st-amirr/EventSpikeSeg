"""Run RTL equivalence only when a real simulator is available."""

import platform
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if shutil.which("ghdl") is None:
        install_hint = {
            "Darwin": "brew install ghdl",
            "Windows": "winget install --exact --id ghdl.ghdl.ucrt64.mcode",
        }.get(platform.system(), "install GHDL with your system package manager")
        print(f"BLOCKED: GHDL is unavailable. Suggested setup: {install_hint}")
        return 2
    root = Path(__file__).resolve().parents[1]
    return subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "verification/cocotb/test_rtl_runner.py"],
        cwd=root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
