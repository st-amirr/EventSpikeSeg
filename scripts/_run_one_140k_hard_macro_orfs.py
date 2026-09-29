#!/usr/bin/env python3
"""Run one exact 140k hard-macro ORFS job without the single-active journal gate.

Used by run_140k_hard_macro_parallel.py so multiple masters can layout concurrently.
Journal updates are merge-safe under an exclusive lock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_xl_hard_macro_orfs import (  # noqa: E402
    _archive_attempt,
    _completed_view_hashes,
    _config_text,
    _generation_command,
    _load_catalog,
    _load_generation,
    _now,
    _run_container,
    _sha256,
    _stage_views,
    _validate_route_reports,
)


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


def _merge_entry(journal_path: Path, module: str, updates: dict) -> dict:
    with JournalLock(journal_path):
        journal = (
            json.loads(journal_path.read_text(encoding="utf-8"))
            if journal_path.is_file()
            else {"schema_version": 1, "masters": {}}
        )
        entries = journal.setdefault("masters", {})
        entry = entries.setdefault(module, {})
        _archive_attempt(entry)
        entry.update(updates)
        journal["updated_at"] = _now()
        temporary = journal_path.with_name(f".{journal_path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        temporary.replace(journal_path)
        return dict(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--generation-table", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--memory", default="8g")
    parser.add_argument("--memory-swap", default="12g")
    parser.add_argument("--cpus", type=float, default=5.0)
    parser.add_argument("--orfs-image", default="openroad/orfs:latest")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    catalog_path = (root / args.catalog).resolve()
    generation_path = (root / args.generation_table).resolve()
    state_dir = (root / args.state_dir).resolve()
    catalog, masters = _load_catalog(catalog_path)
    generation = _load_generation(generation_path)
    module = args.module
    if module not in masters:
        raise SystemExit(f"unknown module {module}")

    journal_path = state_dir / "journal.json"
    with JournalLock(journal_path):
        journal = (
            json.loads(journal_path.read_text(encoding="utf-8"))
            if journal_path.is_file()
            else {"schema_version": 1, "masters": {}}
        )
        entry = journal.setdefault("masters", {}).get(module, {})
        completed = _completed_view_hashes(root, module, masters[module], entry)
        if completed is not None and entry.get("status") == "complete":
            print(f"{module}: already complete")
            return 0

    catalog_sha = _sha256(catalog_path)
    generation_sha = _sha256(generation_path)
    _merge_entry(
        journal_path,
        module,
        {
            "status": "generating_rtl",
            "started_at": _now(),
            "attempts": int(entry.get("attempts", 0)) + 1,
            "catalog_sha256": catalog_sha,
            "generation_table_sha256": generation_sha,
        },
    )

    row = generation[module]
    subprocess.run(_generation_command(row["generation_command"], root), cwd=root, check=True)
    rtl = root / row["implementation_rtl"]
    if not rtl.is_file() or rtl.stat().st_size == 0:
        raise FileNotFoundError(f"generation did not produce {rtl}")

    flow_variant = "hard_macro_exact"
    config = state_dir / "configs" / f"{module}.mk"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        _config_text(module, row["kind"], row["implementation_rtl"], flow_variant),
        encoding="utf-8",
    )
    short_hash = hashlib.sha256(module.encode()).hexdigest()[:10]
    container = f"eventspikeseg-hm-{short_hash}"
    subprocess.run(["docker", "rm", "-f", container], cwd=root, capture_output=True)
    log_path = state_dir / "logs" / f"{module}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _merge_entry(
        journal_path,
        module,
        {
            "status": "running_orfs",
            "rtl_sha256": _sha256(rtl),
            "config": str(config.relative_to(root)).replace("\\", "/"),
            "config_sha256": _sha256(config),
            "resources": {
                "memory": args.memory,
                "memory_swap": args.memory_swap,
                "cpus": args.cpus,
            },
        },
    )

    returncode, evidence = _run_container(
        root=root,
        config=config,
        container=container,
        image=args.orfs_image,
        memory=args.memory,
        memory_swap=args.memory_swap,
        cpus=args.cpus,
        log_path=log_path,
    )
    if returncode != 0:
        _merge_entry(
            journal_path,
            module,
            {
                "status": "oom" if evidence["oom_killed"] else "failed",
                "orfs": evidence,
                "finished_at": _now(),
            },
        )
        print(f"{module}: failed (exit {returncode})", file=sys.stderr)
        subprocess.run(["docker", "rm", "-f", container], cwd=root, check=False)
        return returncode or 1

    try:
        report_hashes = _validate_route_reports(root, module, flow_variant)
        view_hashes = _stage_views(
            root,
            module,
            masters[module],
            root / "artifacts/OpenROAD/results/asap7" / module / flow_variant,
        )
    except Exception as error:
        _merge_entry(
            journal_path,
            module,
            {
                "status": "post_route_validation_failed",
                "orfs": evidence,
                "error": repr(error),
                "finished_at": _now(),
            },
        )
        raise

    _merge_entry(
        journal_path,
        module,
        {
            "status": "complete",
            "orfs": evidence,
            "report_sha256": report_hashes,
            "view_sha256": view_hashes,
            "finished_at": _now(),
        },
    )
    subprocess.run(["docker", "rm", "-f", container], cwd=root, check=False)
    report = root / "artifacts/OpenROAD/logs/asap7" / module / flow_variant / "6_report.json"
    if report.is_file():
        metrics = json.loads(report.read_text(encoding="utf-8"))
        print(
            json.dumps(
                {
                    "setup_slack_ps": metrics.get("finish__timing__setup__ws"),
                    "hold_slack_ps": metrics.get("finish__timing__hold__ws"),
                    "fmax_mhz": (metrics.get("finish__timing__fmax") or 0) / 1e6,
                    "standard_cell_area_um2": metrics.get(
                        "finish__design__instance__area"
                    ),
                },
                indent=2,
            )
        )
    print(f"{module}: complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
