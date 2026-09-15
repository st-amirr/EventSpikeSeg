#!/usr/bin/env python3
"""Run exact XL hard-macro ORFS views resumably and with bounded resources."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _archive_attempt(entry: dict[str, Any]) -> None:
    if not entry.get("status"):
        return
    snapshot = {key: value for key, value in entry.items() if key != "history"}
    entry.setdefault("history", []).append(snapshot)


def _load_catalog(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    masters = {str(master["module"]): master for master in catalog["masters"]}
    if len(masters) != len(catalog["masters"]):
        raise ValueError("catalog contains duplicate master module names")
    return catalog, masters


def _load_generation(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = {str(row["module"]): row for row in csv.DictReader(stream, delimiter="\t")}
    if not rows:
        raise ValueError("master generation table is empty")
    return rows


def _view_is_valid(module: str, kind: str, path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    if kind == "gds":
        return path.stat().st_size >= 100
    text = path.read_text(encoding="utf-8", errors="ignore")
    if kind == "lef":
        return re.search(rf"(?m)^\s*MACRO\s+{re.escape(module)}\s*$", text) is not None
    if kind == "lib":
        return (
            re.search(
                rf"\bcell\s*\(\s*[\"']?{re.escape(module)}[\"']?\s*\)",
                text,
            )
            is not None
        )
    raise ValueError(f"unsupported view kind: {kind}")


def _completed_view_hashes(
    root: Path, module: str, master: dict[str, Any], entry: dict[str, Any]
) -> dict[str, str] | None:
    expected = entry.get("view_sha256", {})
    if entry.get("status") != "complete" or not expected:
        return None
    result: dict[str, str] = {}
    for kind in ("lef", "gds", "lib"):
        path = root / str(master["views"][kind])
        if not _view_is_valid(module, kind, path):
            return None
        digest = _sha256(path)
        if expected and expected.get(kind) != digest:
            return None
        result[kind] = digest
    return result


def _generation_command(command: str, root: Path) -> list[str]:
    arguments = shlex.split(command, posix=True)
    if not arguments or arguments[0] not in {"python", "python3"}:
        raise ValueError("generation command must invoke a checked-in Python script")
    if len(arguments) < 2 or not arguments[1].startswith("scripts/"):
        raise ValueError("generation command must target scripts/")
    arguments[0] = sys.executable
    script = (root / arguments[1]).resolve()
    if root not in script.parents or not script.is_file():
        raise ValueError("generation script escaped or is missing from the project")
    arguments[1] = str(script)
    return arguments


def _config_text(module: str, kind: str, rtl: str, flow_variant: str) -> str:
    if kind == "actor_tile":
        sources = [
            "$(PROJECT_DIR)/asic/rtl/resident_convolution_synapses.sv",
            "$(PROJECT_DIR)/asic/rtl/resident_plif_population.sv",
            "$(PROJECT_DIR)/asic/rtl/resident_retinotopic_plif_population.sv",
            "$(PROJECT_DIR)/asic/rtl/resident_channelized_plif_actor.sv",
        ]
        constraint = "orfs_asap7_resident_tile_constraint.sdc"
    elif kind == "readout_tile":
        sources = ["$(PROJECT_DIR)/asic/rtl/resident_temporal_class_readout.sv"]
        constraint = "orfs_asap7_resident_readout_tile_constraint.sdc"
    else:
        raise ValueError(f"unsupported master kind: {kind}")
    sources.append(f"$(PROJECT_DIR)/{rtl}")
    continuation = " " + chr(92) + "\n  "
    source_lines = continuation.join(sources)
    return f"""export DESIGN_NAME = {module}
export PLATFORM = asap7
export FLOW_VARIANT = {flow_variant}

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := /workspace

export VERILOG_FILES = \\
  {source_lines}
export SDC_FILE = $(PROJECT_DIR)/asic/{constraint}
export CLOCK_PORT = clk
export CLOCK_PERIOD = 5000
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 2
export PLACE_DENSITY = 0.60
export SKIP_CTS_REPAIR_TIMING = 1
export ADDER_MAP_FILE =
export SLEW_MARGIN = 50
export SYNTH_OPERATIONS_ARGS = -noalumacc
export ABC_AREA = 1
"""


def _orfs_config_value(config: Path, variable: str) -> str | None:
    pattern = re.compile(
        rf"(?m)^\s*(?:export\s+)?{re.escape(variable)}\s*(?::|\?)?=\s*([^#\r\n]+)"
    )
    match = pattern.search(config.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def _run_container(
    *,
    root: Path,
    config: Path,
    container: str,
    image: str,
    memory: str,
    memory_swap: str,
    cpus: float,
    log_path: Path,
) -> tuple[int, dict[str, Any]]:
    output = root / "artifacts" / "OpenROAD"
    for directory in ("logs", "objects", "reports", "results"):
        (output / directory).mkdir(parents=True, exist_ok=True)
    config_in_container = "/workspace/" + config.relative_to(root).as_posix()
    make = f"DESIGN_CONFIG={shlex.quote(config_in_container)}"
    shell_command = (
        f"make -C /OpenROAD-flow-scripts/flow {make} && "
        f"make -C /OpenROAD-flow-scripts/flow {make} do-generate_abstract"
    )
    command = [
        "docker", "run", "--name", container, "--platform", "linux/amd64",
        "--memory", memory, "--memory-swap", memory_swap, "--cpus", str(cpus),
        "--volume", f"{root}:/workspace:ro",
    ]
    for directory in ("logs", "objects", "reports", "results"):
        command.extend(
            [
                "--volume",
                f"{output / directory}:/OpenROAD-flow-scripts/flow/{directory}",
            ]
        )
    command.extend([image, "bash", "-lc", shell_command])
    with log_path.open("w", encoding="utf-8") as stream:
        process = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
    inspect = subprocess.run(
        ["docker", "inspect", container, "--format", "{{json .State}}"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    state = json.loads(inspect.stdout) if inspect.returncode == 0 else {}
    log_text = log_path.read_text(encoding="utf-8", errors="ignore")
    peaks = [int(value) for value in re.findall(r"Peak memory:\s*(\d+)KB", log_text)]
    evidence = {
        "container": container,
        "exit_code": process.returncode,
        "docker_state": state,
        "oom_killed": bool(state.get("OOMKilled", False)),
        "peak_memory_kb": max(peaks, default=None),
        "log": str(log_path.relative_to(root)).replace("\\", "/"),
        "log_sha256": _sha256(log_path),
    }
    return process.returncode, evidence


def _inspect_existing_container(
    root: Path,
    container: str,
    log_path: Path,
) -> dict[str, Any]:
    inspect = subprocess.run(
        ["docker", "inspect", container],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    metadata = json.loads(inspect.stdout)[0]
    logs = subprocess.run(
        ["docker", "logs", container],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(logs.stdout + logs.stderr, encoding="utf-8")
    log_text = log_path.read_text(encoding="utf-8", errors="ignore")
    peaks = [int(value) for value in re.findall(r"Peak memory:\s*(\d+)KB", log_text)]
    host = metadata.get("HostConfig", {})
    state = metadata.get("State", {})
    return {
        "container": container,
        "exit_code": state.get("ExitCode"),
        "docker_state": state,
        "oom_killed": bool(state.get("OOMKilled", False)),
        "peak_memory_kb": max(peaks, default=None),
        "resources": {
            "memory_bytes": host.get("Memory"),
            "memory_swap_bytes": host.get("MemorySwap"),
            "nano_cpus": host.get("NanoCpus"),
        },
        "image": metadata.get("Config", {}).get("Image"),
        "command": metadata.get("Config", {}).get("Cmd"),
        "log": str(log_path.relative_to(root)).replace("\\", "/"),
        "log_sha256": _sha256(log_path),
    }


def _adopted_status(evidence: dict[str, Any]) -> str:
    state = evidence.get("docker_state", {})
    if state.get("Running"):
        return "running_external"
    if evidence.get("oom_killed"):
        return "oom"
    if state.get("Status") == "exited" and int(state.get("ExitCode", 1)) == 0:
        return "ready_to_finalize"
    return "failed"


def _run_generate_abstract_container(
    *,
    root: Path,
    config: Path,
    container: str,
    image: str,
    memory_bytes: int | None,
    memory_swap_bytes: int | None,
    nano_cpus: int | None,
    log_path: Path,
) -> dict[str, Any]:
    """Run only ORFS's abstract-view target against completed route outputs."""
    output = root / "artifacts" / "OpenROAD"
    helper = f"{container}-abstract"
    config_in_container = "/workspace/" + config.relative_to(root).as_posix()
    command = ["docker", "run", "--rm", "--name", helper, "--platform", "linux/amd64"]
    if memory_bytes:
        command.extend(["--memory", str(memory_bytes)])
    if memory_swap_bytes:
        command.extend(["--memory-swap", str(memory_swap_bytes)])
    if nano_cpus:
        command.extend(["--cpus", str(nano_cpus / 1_000_000_000)])
    command.extend(["--volume", f"{root}:/workspace:ro"])
    for directory in ("logs", "objects", "reports", "results"):
        path = output / directory
        path.mkdir(parents=True, exist_ok=True)
        command.extend(
            ["--volume", f"{path}:/OpenROAD-flow-scripts/flow/{directory}"]
        )
    make_variable = f"DESIGN_CONFIG={shlex.quote(config_in_container)}"
    command.extend(
        [
            image,
            "bash",
            "-lc",
            "make -C /OpenROAD-flow-scripts/flow "
            f"{make_variable} do-generate_abstract",
        ]
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as stream:
        process = subprocess.run(
            command, cwd=root, stdout=stream, stderr=subprocess.STDOUT
        )
    return {
        "container": helper,
        "exit_code": process.returncode,
        "log": str(log_path.relative_to(root)).replace("\\", "/"),
        "log_sha256": _sha256(log_path),
    }


def _find_result(result_dir: Path, kind: str) -> Path | None:
    preferred = [result_dir / f"6_final.{kind}", result_dir / f"6_1_merged.{kind}"]
    for path in preferred:
        if path.is_file() and path.stat().st_size:
            return path
    candidates = sorted(
        (path for path in result_dir.rglob(f"*.{kind}") if path.stat().st_size),
        key=lambda path: (path.stat().st_mtime_ns, path.stat().st_size),
        reverse=True,
    )
    if candidates:
        return candidates[0]
    compressed = sorted(result_dir.rglob(f"*.{kind}.gz"))
    return compressed[-1] if compressed else None


def _result_view_is_valid(result_dir: Path, module: str, kind: str) -> bool:
    source = _find_result(result_dir, kind)
    if source is None:
        return False
    if source.suffix != ".gz":
        return _view_is_valid(module, kind, source)
    temporary = result_dir / f".{module}.{kind}.{os.getpid()}.validation"
    try:
        with gzip.open(source, "rb") as input_stream, temporary.open(
            "wb"
        ) as output_stream:
            shutil.copyfileobj(input_stream, output_stream)
        return _view_is_valid(module, kind, temporary)
    finally:
        temporary.unlink(missing_ok=True)


def _stage_views(
    root: Path,
    module: str,
    master: dict[str, Any],
    result_dir: Path,
) -> dict[str, str]:
    destinations = {
        kind: root / str(master["views"][kind]) for kind in ("lef", "gds", "lib")
    }
    destination_parents = {path.parent for path in destinations.values()}
    if len(destination_parents) != 1:
        raise ValueError("all hard-macro views must share one destination directory")
    destination_dir = destination_parents.pop()
    staging_dir = destination_dir.with_name(
        f".{destination_dir.name}.{os.getpid()}.staging"
    )
    backup_dir = destination_dir.with_name(
        f".{destination_dir.name}.{os.getpid()}.backup"
    )
    if staging_dir.exists() or backup_dir.exists():
        raise FileExistsError("stale hard-macro view staging directory exists")
    staging_dir.mkdir(parents=True)
    hashes: dict[str, str] = {}
    try:
        for kind in ("lef", "gds", "lib"):
            source = _find_result(result_dir, kind)
            if source is None:
                raise FileNotFoundError(
                    f"ORFS did not produce a {kind} view in {result_dir}"
                )
            destination = staging_dir / destinations[kind].name
            if source.suffix == ".gz":
                with gzip.open(source, "rb") as input_stream, destination.open(
                    "wb"
                ) as output_stream:
                    shutil.copyfileobj(input_stream, output_stream)
            else:
                shutil.copyfile(source, destination)
            if not _view_is_valid(module, kind, destination):
                raise ValueError(f"generated {kind} does not declare {module}")
            hashes[kind] = _sha256(destination)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    destination_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        if destination_dir.exists():
            destination_dir.replace(backup_dir)
        staging_dir.replace(destination_dir)
    except Exception:
        if backup_dir.exists() and not destination_dir.exists():
            backup_dir.replace(destination_dir)
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    shutil.rmtree(backup_dir, ignore_errors=True)
    return hashes


def _validate_route_reports(
    root: Path,
    module: str,
    flow_variant: str,
) -> dict[str, str]:
    output = root / "artifacts" / "OpenROAD"
    report = output / "logs" / "asap7" / module / flow_variant / "6_report.json"
    drc = output / "reports" / "asap7" / module / flow_variant / "5_route_drc.rpt"
    subprocess.run(
        [
            sys.executable,
            str(root / "asic" / "scripts" / "check_orfs_reports.py"),
            str(report),
            str(drc),
            "--time-unit",
            "ps",
        ],
        cwd=root,
        check=True,
    )
    return {"route_report": _sha256(report), "drc_report": _sha256(drc)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("artifacts/ASIC_XL/hard_hierarchy/hard_macro_catalog.json"),
    )
    parser.add_argument(
        "--generation-table",
        type=Path,
        default=Path(
            "artifacts/ASIC_XL/hard_hierarchy/hard_macro_master_generation.tsv"
        ),
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("artifacts/ASIC_XL/hard_macro_orfs"),
    )
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--kind", choices=("actor_tile", "readout_tile"))
    parser.add_argument("--max-masters", type=int, default=1)
    parser.add_argument("--memory", default="12g")
    parser.add_argument("--memory-swap", default="20g")
    parser.add_argument("--cpus", type=float, default=2.0)
    parser.add_argument("--orfs-image", default="openroad/orfs:latest")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--adopt-container")
    parser.add_argument("--adopt-config", type=Path)
    parser.add_argument("--adopt-design-name")
    parser.add_argument("--adopt-flow-variant")
    parser.add_argument("--keep-containers", action="store_true")
    args = parser.parse_args()
    if args.max_masters < 1 or args.cpus <= 0:
        parser.error("max-masters and cpus must be positive")

    root = Path(__file__).resolve().parents[1]
    catalog_path = (root / args.catalog).resolve()
    generation_path = (root / args.generation_table).resolve()
    state_dir = (root / args.state_dir).resolve()
    catalog, masters = _load_catalog(catalog_path)
    generation = _load_generation(generation_path)
    if set(masters) != set(generation):
        raise ValueError("catalog and generation table master sets differ")
    journal_path = state_dir / "journal.json"
    journal = (
        json.loads(journal_path.read_text(encoding="utf-8"))
        if journal_path.is_file()
        else {"schema_version": 1, "masters": {}}
    )
    journal["catalog_sha256"] = _sha256(catalog_path)
    journal["generation_table_sha256"] = _sha256(generation_path)
    entries = journal.setdefault("masters", {})
    obsolete = journal.setdefault("obsolete_masters", {})
    for name in sorted(set(entries) - set(masters)):
        obsolete[name] = entries.pop(name)
    for name, master in masters.items():
        entry = entries.get(name, {})
        hashes = _completed_view_hashes(root, name, master, entry)
        if hashes is not None and entry.get("status") == "complete":
            entry.update(
                {
                    "catalog_sha256": journal["catalog_sha256"],
                    "generation_table_sha256": journal["generation_table_sha256"],
                    "view_sha256": hashes,
                }
            )
    journal["obsolete_master_count"] = len(obsolete)
    journal["updated_at"] = _now()
    journal["catalog_scope"] = catalog.get("scope")
    _atomic_json(journal_path, journal)
    selected = [name for name in masters if not args.module or name in args.module]
    if args.module and set(args.module) - set(masters):
        raise ValueError(f"unknown modules: {sorted(set(args.module) - set(masters))}")
    if args.kind:
        selected = [name for name in selected if masters[name]["kind"] == args.kind]
    if args.adopt_container:
        if len(selected) != 1 or not args.module:
            parser.error("--adopt-container requires exactly one --module")
        module = selected[0]
        log_path = state_dir / "logs" / f"{module}.adopted.log"
        evidence = _inspect_existing_container(root, args.adopt_container, log_path)
        entry = entries.setdefault(module, {})
        docker_state = evidence["docker_state"]
        adopted_status = _adopted_status(evidence)
        same_attempt = (
            entry.get("adopted") is True
            and entry.get("orfs", {}).get("container") == args.adopt_container
            and entry.get("started_at") == docker_state.get("StartedAt")
        )
        if not same_attempt:
            _archive_attempt(entry)
        entry.update(
            {
                "status": adopted_status,
                "attempts": int(entry.get("attempts", 0)) + (0 if same_attempt else 1),
                "catalog_sha256": journal["catalog_sha256"],
                "generation_table_sha256": journal["generation_table_sha256"],
                "started_at": docker_state.get("StartedAt"),
                "finished_at": (
                    None if docker_state.get("Running") else docker_state.get("FinishedAt")
                ),
                "orfs": evidence,
                "adopted": True,
            }
        )
        _atomic_json(journal_path, journal)
        if adopted_status == "running_external":
            print(f"{module}: refreshed running_external evidence")
            return
        if adopted_status == "oom":
            print(
                f"{module}: adopted {adopted_status} evidence "
                f"(exit {evidence.get('exit_code')})",
                file=sys.stderr,
            )
            raise SystemExit(
                137
            )

        config = None
        if args.adopt_config is not None:
            config = (root / args.adopt_config).resolve()
            if root not in config.parents or not config.is_file():
                raise ValueError("adopt config escaped or is missing from the project")
        design_name = (
            args.adopt_design_name
            or (_orfs_config_value(config, "DESIGN_NAME") if config else None)
            or module
        )
        flow_variant = (
            args.adopt_flow_variant
            or (_orfs_config_value(config, "FLOW_VARIANT") if config else None)
            or "hard_macro_exact"
        )
        if design_name != module:
            entry.update(
                {
                    "status": "post_route_validation_failed",
                    "error": (
                        "adopted ORFS DESIGN_NAME does not match the catalog "
                        "hard-macro "
                        f"module: {design_name!r} != {module!r}"
                    ),
                    "finished_at": _now(),
                }
            )
            _atomic_json(journal_path, journal)
            raise ValueError(entry["error"])
        result_dir = (
            root
            / "artifacts"
            / "OpenROAD"
            / "results"
            / "asap7"
            / design_name
            / flow_variant
        )
        if adopted_status == "failed":
            try:
                recovered_report_hashes = _validate_route_reports(
                    root, design_name, flow_variant
                )
                if not _result_view_is_valid(result_dir, module, "gds"):
                    raise ValueError(
                        "adopted container failed and has no valid final GDS"
                    )
            except Exception:
                print(
                    f"{module}: adopted failed evidence "
                    f"(exit {evidence.get('exit_code')})",
                    file=sys.stderr,
                )
                raise SystemExit(int(evidence.get("exit_code") or 1))
            entry.update(
                {
                    "status": "ready_to_finalize",
                    "report_sha256": recovered_report_hashes,
                    "recovered_post_route_exit_code": evidence.get("exit_code"),
                }
            )
            _atomic_json(journal_path, journal)
        try:
            entry["report_sha256"] = _validate_route_reports(
                root, design_name, flow_variant
            )
            missing = [
                kind
                for kind in ("lef", "gds", "lib")
                if not _result_view_is_valid(result_dir, module, kind)
            ]
            if missing:
                if config is None:
                    raise ValueError(
                        "abstract views are missing; pass --adopt-config to run only "
                        "ORFS do-generate_abstract"
                    )
                resources = evidence.get("resources", {})
                abstract_log = state_dir / "logs" / f"{module}.abstract.log"
                abstract = _run_generate_abstract_container(
                    root=root,
                    config=config,
                    container=args.adopt_container,
                    image=str(evidence.get("image") or args.orfs_image),
                    memory_bytes=resources.get("memory_bytes"),
                    memory_swap_bytes=resources.get("memory_swap_bytes"),
                    nano_cpus=resources.get("nano_cpus"),
                    log_path=abstract_log,
                )
                entry["abstract"] = abstract
                _atomic_json(journal_path, journal)
                if abstract["exit_code"] != 0:
                    raise RuntimeError(
                        "ORFS do-generate_abstract failed with exit "
                        f"{abstract['exit_code']}"
                    )
            view_hashes = _stage_views(root, module, masters[module], result_dir)
        except Exception as error:
            entry.update(
                {
                    "status": "post_route_validation_failed",
                    "error": repr(error),
                    "finished_at": _now(),
                }
            )
            _atomic_json(journal_path, journal)
            raise
        entry.update(
            {
                "status": "complete",
                "view_sha256": view_hashes,
                "finished_at": _now(),
            }
        )
        journal["updated_at"] = _now()
        journal["catalog_scope"] = catalog.get("scope")
        _atomic_json(journal_path, journal)
        if not args.keep_containers:
            subprocess.run(
                ["docker", "rm", args.adopt_container], cwd=root, check=False
            )
        print(f"{module}: adopted and complete")
        return
    if args.list:
        for name in selected:
            entry = entries.get(name, {})
            hashes = _completed_view_hashes(root, name, masters[name], entry)
            status = "complete" if hashes else str(entry.get("status", "pending"))
            print(f"{status}\t{masters[name]['kind']}\t{name}")
        return

    active = [
        name
        for name, entry in entries.items()
        if name in masters and str(entry.get("status", "")).startswith("running")
    ]
    if active:
        raise RuntimeError(
            "journal records active ORFS work; refresh/adopt it before launching more: "
            + ", ".join(active)
        )

    attempted = 0
    for module in selected:
        entry = entries.setdefault(module, {})
        provenance_matches = (
            entry.get("catalog_sha256") == journal["catalog_sha256"]
            and entry.get("generation_table_sha256")
            == journal["generation_table_sha256"]
        )
        completed = (
            _completed_view_hashes(root, module, masters[module], entry)
            if provenance_matches
            else None
        )
        if completed is not None:
            entry.update({"status": "complete", "view_sha256": completed})
            continue
        if attempted >= args.max_masters:
            continue
        attempted += 1
        row = generation[module]
        _archive_attempt(entry)
        entry.update(
            {
                "status": "generating_rtl",
                "started_at": _now(),
                "attempts": int(entry.get("attempts", 0)) + 1,
                "catalog_sha256": journal["catalog_sha256"],
                "generation_table_sha256": journal["generation_table_sha256"],
            }
        )
        _atomic_json(journal_path, journal)
        try:
            subprocess.run(
                _generation_command(row["generation_command"], root),
                cwd=root,
                check=True,
            )
        except Exception as error:
            entry.update(
                {
                    "status": "rtl_generation_failed",
                    "error": repr(error),
                    "finished_at": _now(),
                }
            )
            _atomic_json(journal_path, journal)
            raise
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
        entry.update(
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
            }
        )
        _atomic_json(journal_path, journal)
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
        entry["orfs"] = evidence
        if returncode != 0:
            entry.update(
                {
                    "status": "oom" if evidence["oom_killed"] else "failed",
                    "finished_at": _now(),
                }
            )
            _atomic_json(journal_path, journal)
            print(f"{module}: {entry['status']} (exit {returncode})", file=sys.stderr)
            returncode = 137 if evidence["oom_killed"] else returncode
            raise SystemExit(returncode)
        try:
            entry["report_sha256"] = _validate_route_reports(
                root, module, flow_variant
            )
            result_dir = (
                root
                / "artifacts"
                / "OpenROAD"
                / "results"
                / "asap7"
                / module
                / flow_variant
            )
            view_hashes = _stage_views(root, module, masters[module], result_dir)
        except Exception as error:
            entry.update(
                {
                    "status": "post_route_validation_failed",
                    "error": repr(error),
                    "finished_at": _now(),
                }
            )
            _atomic_json(journal_path, journal)
            raise
        entry.update(
            {
                "status": "complete",
                "view_sha256": view_hashes,
                "finished_at": _now(),
            }
        )
        _atomic_json(journal_path, journal)
        if not args.keep_containers:
            subprocess.run(["docker", "rm", container], cwd=root, check=False)
        print(f"{module}: complete")
    journal["updated_at"] = _now()
    journal["catalog_scope"] = catalog.get("scope")
    _atomic_json(journal_path, journal)


if __name__ == "__main__":
    main()
