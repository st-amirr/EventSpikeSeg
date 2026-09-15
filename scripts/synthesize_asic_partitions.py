"""Resume independent XL actor synthesis with bounded Linux virtual address space.

Run in the verification Docker image against an already prepared XL export.
The synthesis commands and source hashes match run_xl_partitioned_synthesis.sh.
"""

import argparse
import errno
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

RTL = [
    f"asic/rtl/{name}.sv"
    for name in (
        "resident_convolution_synapses",
        "resident_plif_population",
        "retinotopic_mechanism_update",
        "resident_retinotopic_plif_population",
        "resident_channelized_plif_actor",
        "tiled_resident_channelized_plif_actor",
    )
]
_PRINT_LOCK = threading.Lock()
_TRANSIENT_IO = {errno.EIO, errno.EAGAIN, errno.EBUSY, errno.EINTR, getattr(errno, "ESTALE", 116)}


def report(message):
    with _PRINT_LOCK:
        print(message, flush=True)


def atomic_write(path, text, attempts=3):
    """Retry transient filesystem errors, then propagate permanent failure."""
    temporary = path.with_name(path.name + ".tmp")
    for attempt in range(attempts):
        try:
            with temporary.open("w") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(path)
            return
        except OSError as error:
            if error.errno not in _TRANSIENT_IO or attempt + 1 == attempts:
                raise
            report(f"STORAGE RETRY {path.name}: {error} ({attempt + 1}/{attempts})")
            time.sleep(0.25 * (attempt + 1))


def failure_kind(returncode, text):
    lower = text.lower()
    if any(
        marker in lower
        for marker in ("input/output error", "no space left on device", "read-only file system")
    ):
        return "STORAGE_ERROR"
    if any(
        marker in lower
        for marker in (
            "std::bad_alloc",
            "out of memory",
            "cannot allocate memory",
            "failed to allocate",
        )
    ):
        return "MEMORY"
    # SIGABRT/SIGKILL alone do not prove memory exhaustion.
    return "SYNTHESIS_ERROR"


def memory_status(limit, retry_limit):
    return "MEMORY_RETRY_PENDING" if limit < retry_limit else "MEMORY_FINAL"


def saved_memory_limit(journal, expected):
    if not journal.is_file():
        return 0
    try:
        record = json.loads(journal.read_text())
        if not isinstance(record, dict) or not isinstance(record.get("status"), str):
            return 0
        if record.get("signature") == expected and record.get("status", "").startswith("MEMORY_"):
            return int(record["virtual_memory_gib"])
    except (ValueError, KeyError, TypeError):
        pass  # An incomplete/old journal cannot authorize reuse.
    return 0


def no_core_environment():
    """Load the guard after exec: pre-exec prctl is reset by execve on Linux."""
    installed = os.environ.get("SYNTHESIS_NO_CORE_LIBRARY")
    if installed:
        if not Path(installed).is_file():
            raise RuntimeError(f"Missing synthesis core guard: {installed}")
        environment = os.environ.copy()
        environment["LD_PRELOAD"] = installed + (
            ":" + environment["LD_PRELOAD"] if environment.get("LD_PRELOAD") else ""
        )
        return None, environment
    cache = tempfile.TemporaryDirectory(prefix="synthesis-no-core-")
    library = str(Path(cache.name) / "no_core_dump.so")
    source = Path(__file__).resolve().parents[1] / "asic/tools/no_core_dump.c"
    try:
        subprocess.run(["cc", "-shared", "-fPIC", "-O2", "-o", library, str(source)], check=True)
    except Exception:
        cache.cleanup()
        raise
    environment = os.environ.copy()
    environment["LD_PRELOAD"] = library + (
        ":" + environment["LD_PRELOAD"] if environment.get("LD_PRELOAD") else ""
    )
    return cache, environment


def signature(paths):
    return hashlib.sha256(subprocess.check_output(["sha256sum", *map(str, paths)])).hexdigest()


def passed(log, stamp, expected):
    if not log.is_file() or not stamp.is_file() or stamp.read_text().strip() != expected:
        return False
    text = log.read_text(errors="replace")
    return "End of script" in text and not any(
        line.startswith("ERROR:") for line in text.splitlines()
    )


def main():
    import fcntl
    import resource

    # Set before any threads/children; inherited by generators, attention and Yosys.
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument(
        "--worker-memory-gib", type=int, default=8, help="worker virtual address space limit"
    )
    parser.add_argument(
        "--retry-memory-gib", type=int, default=24, help="serial virtual address space limit"
    )
    parser.add_argument("--tile-width", type=int, default=2)
    parser.add_argument("--tile-height", type=int, default=2)
    parser.add_argument("--actors", nargs="+")
    parser.add_argument("--summary-name", default="summary.tsv")
    parser.add_argument(
        "--no-resume", action="store_true", help="ignore saved passes and memory failures"
    )
    args = parser.parse_args()
    if (
        min(
            args.workers,
            args.worker_memory_gib,
            args.retry_memory_gib,
            args.tile_width,
            args.tile_height,
        )
        < 1
    ):
        parser.error("workers, memory limits, and tile dimensions must be positive")
    guard_cache, child_environment = no_core_environment()
    spec = args.export / "model_spec.yaml"
    actors = json.loads(spec.read_text())["graph"]["actor_topological_order"]
    if len(actors) != 44 or len(set(actors)) != 44:
        parser.error("expected 44 distinct XL actors")
    if args.actors:
        if set(args.actors) - set(actors):
            parser.error("unknown actor selection")
        actors = [actor for actor in actors if actor in args.actors]
    log_dir = args.export / f"partitioned_synthesis_{args.tile_width}x{args.tile_height}"
    log_dir.mkdir(parents=True, exist_ok=True)
    lock = (log_dir / "parallel.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    summary = log_dir / args.summary_name
    statuses = {
        actor: ("PENDING", log_dir / (actor.replace(".", "_") + ".log")) for actor in actors
    }
    storage_errors = []

    def save():
        rows = ["actor\tstatus\tlog", f"attention\tPASS\t{log_dir / 'attention.log'}"]
        rows.extend(f"{actor}\t{statuses[actor][0]}\t{statuses[actor][1]}" for actor in actors)
        try:
            atomic_write(summary, "\n".join(rows) + "\n")
            return True
        except OSError as error:
            storage_errors.append(str(error))
            report(f"STORAGE_ERROR summary: {error}; actor journals retain completed results")
            return False

    attention_log, attention_stamp = log_dir / "attention.log", log_dir / "attention.sha256"
    attention_signature = signature(["asic/rtl/resident_spike_mask_attention.sv"])
    if args.no_resume or not passed(attention_log, attention_stamp, attention_signature):
        attention_stamp.unlink(missing_ok=True)
        subprocess.run(
            [
                "yosys",
                "-q",
                "-l",
                str(attention_log),
                "-p",
                "read_verilog -sv asic/rtl/resident_spike_mask_attention.sv; "
                "hierarchy -top resident_spike_mask_attention; proc; opt; check",
            ],
            check=True,
            env=child_environment,
        )
        atomic_write(attention_stamp, attention_signature + "\n")
        if not passed(attention_log, attention_stamp, attention_signature):
            attention_stamp.unlink(missing_ok=True)
            raise RuntimeError("attention synthesis has no valid completion marker")
    if not save():
        return 2

    def run_actor(actor, memory_gib):
        safe = actor.replace(".", "_")
        top, log = log_dir / f"{safe}_tile.sv", log_dir / f"{safe}.log"
        stamp, script = log_dir / f"{safe}.sha256", log_dir / f"{safe}.ys"
        journal = log_dir / f"{safe}.status.json"
        expected = None
        try:
            subprocess.run(
                [
                    sys.executable,
                    "scripts/generate_resident_tile_pnr_top.py",
                    str(spec),
                    str(top),
                    "--actor",
                    actor,
                    "--tile-width",
                    str(args.tile_width),
                    "--tile-height",
                    str(args.tile_height),
                ],
                check=True,
                env=child_environment,
            )
            expected = signature([*RTL, top])
            if not args.no_resume and passed(log, stamp, expected):
                report(f"REUSE {actor}")
                return "PASS", log
            previous_limit = 0 if args.no_resume else saved_memory_limit(journal, expected)
            if previous_limit >= memory_gib:
                status = memory_status(previous_limit, args.retry_memory_gib)
                report(
                    f"SKIP {actor}: known memory failure at {previous_limit} GiB "
                    f"virtual address space ({status})"
                )
                return status, log
            stamp.unlink(missing_ok=True)
            atomic_write(
                script,
                "read_verilog -sv "
                + " ".join([*RTL, str(top)])
                + ";\nhierarchy -top resident_actor_tile_pnr_top;\nproc; memory; opt; check\n",
            )
            report(f"START {actor} (virtual address space limit {memory_gib} GiB)")
            console_path = log_dir / f"{safe}.console.log"
            with console_path.open("w") as console:
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        'ulimit -c 0; ulimit -v "$1"; shift; exec "$@"',
                        "synthesis",
                        str(memory_gib * 1024 * 1024),
                        "yosys",
                        "-q",
                        "-l",
                        str(log),
                        "-s",
                        str(script),
                    ],
                    stdout=console,
                    stderr=subprocess.STDOUT,
                    env=child_environment,
                )
            status = failure_kind(result.returncode, console_path.read_text(errors="replace"))
            if result.returncode == 0:
                atomic_write(stamp, expected + "\n")
                if passed(log, stamp, expected):
                    status = "PASS"
                else:
                    stamp.unlink(missing_ok=True)
                    status = "SYNTHESIS_ERROR"
            elif status == "MEMORY":
                status = memory_status(memory_gib, args.retry_memory_gib)
            atomic_write(
                journal,
                json.dumps(
                    {
                        "actor": actor,
                        "signature": expected,
                        "status": status,
                        "virtual_memory_gib": memory_gib,
                        "returncode": result.returncode,
                    }
                )
                + "\n",
            )
            report(f"{status} {actor}: exit {result.returncode}")
            return status, log
        except OSError as error:
            report(f"STORAGE_ERROR {actor}: {error}")
            return "STORAGE_ERROR", log
        except Exception as error:
            report(f"SYNTHESIS_ERROR {actor}: {error}")
            return "SYNTHESIS_ERROR", log

    # Bound queued work as well as active work so persistent storage errors stop
    # new synthesis, while already-running children finish and journal results.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        remaining = iter(actors)
        futures = {}

        def submit_next():
            actor = next(remaining, None)
            if actor is not None:
                futures[pool.submit(run_actor, actor, args.worker_memory_gib)] = actor

        for _ in range(args.workers):
            submit_next()
        while futures:
            future = next(as_completed(futures))
            actor = futures.pop(future)
            statuses[actor] = future.result()
            if statuses[actor][0] == "STORAGE_ERROR":
                storage_errors.append(actor)
            save()
            if not storage_errors:
                submit_next()
    # All parallel processes have exited before a larger-memory retry begins.
    for actor in actors:
        if storage_errors:
            break
        if statuses[actor][0] == "MEMORY_RETRY_PENDING":
            report(f"SERIAL RETRY {actor}")
            statuses[actor] = run_actor(actor, args.retry_memory_gib)
            if statuses[actor][0] == "STORAGE_ERROR":
                storage_errors.append(actor)
            save()
    failed = [actor for actor in actors if statuses[actor][0] != "PASS"]
    outcome = "STOPPED STORAGE_ERROR" if storage_errors else "COMPLETE"
    passed_count = len(actors) - len(failed)
    report(f"{outcome} {passed_count}/{len(actors)} actors passed; unresolved={failed}")
    return 2 if storage_errors else int(bool(failed))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as error:
        report(f"STORAGE_ERROR: {error}")
        raise SystemExit(2) from error
