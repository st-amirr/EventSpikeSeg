#!/usr/bin/env python3
"""Launch multiple 140k hard-macro ORFS workers in parallel.

Masters are independent physical layouts. Default sizing targets a 32 GiB /
16-CPU Docker host: 3 concurrent jobs at 8g RAM and ~5 CPUs each.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


class JournalLock:
    def __init__(self, journal_path: Path) -> None:
        self.path = journal_path.with_name(journal_path.name + ".lock")
        self._fd: int | None = None

    def __enter__(self) -> "JournalLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                self._fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self._fd, str(os.getpid()).encode("ascii"))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 1800:
                        self.path.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                time.sleep(0.05)

    def __exit__(self, *_exc: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self.path.unlink(missing_ok=True)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_journal(path: Path) -> dict[str, Any]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema_version": 1, "masters": {}}


def save_journal(path: Path, journal: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def pending_modules(catalog: dict[str, Any], journal: dict[str, Any]) -> list[str]:
    masters = {m["module"]: m for m in catalog["masters"]}
    entries = journal.setdefault("masters", {})
    ordered = [
        row["module"]
        for row in csv.DictReader(
            (ROOT / "artifacts/ASIC/hard_hierarchy/hard_macro_master_generation.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    ]
    pending: list[str] = []
    for module in ordered:
        if module not in masters:
            continue
        entry = entries.get(module, {})
        status = str(entry.get("status", "pending"))
        if status == "complete":
            views = masters[module]["views"]
            if all(
                (ROOT / path).is_file() and (ROOT / path).stat().st_size > 0
                for path in views.values()
            ):
                continue
        if status.startswith("running"):
            continue
        pending.append(module)
    return pending


def claim_module(journal_path: Path, module: str, worker_id: int) -> bool:
    with JournalLock(journal_path):
        journal = load_journal(journal_path)
        entries = journal.setdefault("masters", {})
        entry = entries.setdefault(module, {})
        status = str(entry.get("status", "pending"))
        if status == "complete" or status.startswith("running"):
            return False
        entry.update(
            {
                "status": "running_orfs_claimed",
                "claimed_by_parallel_worker": worker_id,
                "claimed_at": now(),
            }
        )
        journal["updated_at"] = now()
        save_journal(journal_path, journal)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--memory", default="8g")
    parser.add_argument("--memory-swap", default="12g")
    parser.add_argument("--cpus", type=float, default=5.0)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("artifacts/ASIC/hard_hierarchy/hard_macro_catalog.json"),
    )
    parser.add_argument(
        "--generation-table",
        type=Path,
        default=Path("artifacts/ASIC/hard_hierarchy/hard_macro_master_generation.tsv"),
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("artifacts/ASIC/hard_hierarchy/orfs_state"),
    )
    parser.add_argument("--orfs-image", default="openroad/orfs:latest")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    helper = ROOT / "scripts" / "_run_one_140k_hard_macro_orfs.py"
    if not helper.is_file():
        print(f"missing helper {helper}", file=sys.stderr)
        return 2

    catalog = json.loads((ROOT / args.catalog).read_text(encoding="utf-8"))
    journal_path = ROOT / args.state_dir / "journal.json"
    state_dir = ROOT / args.state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "logs").mkdir(parents=True, exist_ok=True)

    with JournalLock(journal_path):
        queue = pending_modules(catalog, load_journal(journal_path))
    print(
        f"pending={len(queue)} workers={args.workers} "
        f"memory={args.memory} cpus={args.cpus}"
    )
    if args.dry_run:
        for module in queue[:30]:
            print(" ", module)
        if len(queue) > 30:
            print(f"  ... +{len(queue) - 30} more")
        return 0

    live: dict[int, tuple[str, subprocess.Popen[str], Any]] = {}
    next_worker = 0
    idx = 0
    failures = 0
    claimed = 0

    while idx < len(queue) or live:
        # Reap finished workers.
        for wid in list(live):
            module, proc, handle = live[wid]
            code = proc.poll()
            if code is None:
                continue
            handle.close()
            if code != 0:
                failures += 1
                print(f"FAIL {module} exit={code}")
            else:
                print(f"DONE {module}")
            del live[wid]

        while len(live) < args.workers and idx < len(queue):
            module = queue[idx]
            idx += 1
            wid = next_worker
            next_worker += 1
            if not claim_module(journal_path, module, wid):
                print(f"SKIP {module} (already claimed/complete)")
                continue
            claimed += 1
            log = state_dir / "logs" / f"parallel_worker_{module}.out"
            handle = open(log, "w", encoding="utf-8")
            cmd = [
                sys.executable,
                str(helper),
                "--catalog",
                str(args.catalog),
                "--generation-table",
                str(args.generation_table),
                "--state-dir",
                str(args.state_dir),
                "--module",
                module,
                "--memory",
                args.memory,
                "--memory-swap",
                args.memory_swap,
                "--cpus",
                str(args.cpus),
                "--orfs-image",
                args.orfs_image,
            ]
            print(f"START {module} workers_live={len(live)+1} log={log}")
            proc = subprocess.Popen(
                cmd, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, text=True
            )
            live[wid] = (module, proc, handle)

        if live:
            time.sleep(10)

    print(f"claimed={claimed} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
