#!/usr/bin/env python3
"""Generate all checkpoint-exact 140k hard-macro master RTL files from the catalog TSV."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "artifacts/ASIC/hard_hierarchy/hard_macro_master_generation.tsv"
STATUS = ROOT / "artifacts/ASIC/hard_hierarchy/master_rtl_generation_status.json"


def main() -> int:
    rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
    print(f"Generating {len(rows)} masters...", flush=True)
    ok = 0
    failures: list[dict[str, object]] = []
    for index, row in enumerate(rows, 1):
        command = row["generation_command"]
        out = ROOT / row["implementation_rtl"]
        out.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not out.is_file():
            failures.append(
                {
                    "module": row["module"],
                    "returncode": result.returncode,
                    "stderr_tail": (result.stderr or result.stdout)[-800:],
                }
            )
            print(f"FAIL {index}/{len(rows)} {row['module']}", flush=True)
        else:
            ok += 1
            if index % 20 == 0 or index == len(rows):
                print(f"ok {index}/{len(rows)}", flush=True)
    status = {
        "generated": ok,
        "failed": len(failures),
        "total": len(rows),
        "failures": failures,
    }
    STATUS.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: status[k] for k in ("generated", "failed", "total")}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
