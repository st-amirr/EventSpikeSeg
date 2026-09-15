"""Failure/restart regression tests; subprocess mocks never synthesize or crash."""

import errno
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "partition_runner", ROOT / "scripts/synthesize_asic_partitions.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_atomic_write_retries_transient_replace_without_losing_old_file(tmp_path, monkeypatch):
    target = tmp_path / "summary.tsv"
    target.write_text("old")
    original_replace = Path.replace
    calls = []

    def replace(path, destination):
        calls.append(path)
        if len(calls) < 3:
            assert target.read_text() == "old"
            raise OSError(errno.EIO, "temporary I/O fault")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    runner.atomic_write(target, "new")
    assert target.read_text() == "new"
    assert len(calls) == 3


@pytest.mark.parametrize("error_number, expected_calls", [(errno.EIO, 3), (errno.ENOSPC, 1)])
def test_atomic_write_exhaustion_preserves_committed_file(
    tmp_path, monkeypatch, error_number, expected_calls
):
    target = tmp_path / "summary.tsv"
    target.write_text("old")
    replace = Mock(side_effect=OSError(error_number, "injected storage failure"))
    monkeypatch.setattr(Path, "replace", replace)
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    with pytest.raises(OSError) as failure:
        runner.atomic_write(target, "new")
    assert failure.value.errno == error_number
    assert replace.call_count == expected_calls
    assert target.read_text() == "old"


@pytest.mark.parametrize(
    "code,text,expected",
    [
        (-6, "Aborted", "SYNTHESIS_ERROR"),
        (-9, "Killed", "SYNTHESIS_ERROR"),
        (-6, "Assertion failed", "SYNTHESIS_ERROR"),
        (-6, "terminate called after throwing std::bad_alloc", "MEMORY"),
        (1, "Input/output error", "STORAGE_ERROR"),
        (1, "No space left on device; std::bad_alloc", "STORAGE_ERROR"),
    ],
)
def test_failure_classification_requires_evidence(code, text, expected):
    assert runner.failure_kind(code, text) == expected


@pytest.mark.parametrize(
    "record,expected",
    [
        ({"signature": "current", "status": "MEMORY_RETRY_PENDING", "virtual_memory_gib": 8}, 8),
        ({"signature": "current", "status": "MEMORY_FINAL", "virtual_memory_gib": 24}, 24),
        ({"signature": "stale", "status": "MEMORY_FINAL", "virtual_memory_gib": 24}, 0),
        ({"signature": "current", "status": "SYNTHESIS_ERROR", "virtual_memory_gib": 24}, 0),
        ({"signature": "current", "status": "MEMORY_FINAL"}, 0),
        ({"signature": "current", "status": "MEMORY_FINAL", "virtual_memory_gib": "bad"}, 0),
        (None, 0),
        ([], 0),
        ({"signature": "current", "status": None, "virtual_memory_gib": 24}, 0),
    ],
)
def test_saved_memory_limit_is_signature_bound(tmp_path, record, expected):
    journal = tmp_path / "actor.status.json"
    journal.write_text(json.dumps(record))
    assert runner.saved_memory_limit(journal, "current") == expected


def test_missing_and_truncated_journals_do_not_authorize_skip(tmp_path):
    journal = tmp_path / "actor.status.json"
    assert runner.saved_memory_limit(journal, "current") == 0
    journal.write_text('{"signature":')
    assert runner.saved_memory_limit(journal, "current") == 0


@pytest.fixture
def run_fixture(tmp_path, monkeypatch):
    if sys.platform != "linux":
        pytest.skip("runner uses Linux fcntl/resource")
    import resource

    actors = [f"actor{i}" for i in range(44)]
    (tmp_path / "model_spec.yaml").write_text(
        json.dumps({"graph": {"actor_topological_order": actors}})
    )
    logs = tmp_path / "partitioned_synthesis_2x2"
    logs.mkdir()
    (logs / "attention.log").write_text("End of script\n")
    (logs / "attention.sha256").write_text("current\n")
    monkeypatch.setattr(resource, "setrlimit", lambda *_: None)
    monkeypatch.setattr(runner, "no_core_environment", lambda: (Mock(), {}))
    monkeypatch.setattr(runner, "signature", lambda _: "current")
    calls = []
    outcomes = []

    def fake_run(command, **kwargs):
        if command[0] == "yosys":
            Path(command[command.index("-l") + 1]).write_text("End of script\n")
            return subprocess.CompletedProcess(command, 0)
        if command[0] == sys.executable:
            Path(command[3]).write_text("// generated mock top\n")
            return subprocess.CompletedProcess(command, 0)
        assert command[0] == "bash"
        log = Path(command[command.index("-l") + 1])
        calls.append((log.stem, int(command[4]) // (1024 * 1024)))
        code, console, log_text = outcomes.pop(0)
        kwargs["stdout"].write(console)
        log.write_text(log_text)
        return subprocess.CompletedProcess(command, code)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    def invoke(selected=("actor0",), extra=()):
        monkeypatch.setattr(
            sys, "argv", ["runner", str(tmp_path), "--workers", "1", "--actors", *selected, *extra]
        )
        return runner.main()

    return logs, calls, outcomes, invoke


def test_memory_failure_retries_serially_at_larger_limit(run_fixture):
    logs, calls, outcomes, invoke = run_fixture
    outcomes.extend([(-6, "std::bad_alloc", "partial"), (0, "", "End of script\n")])
    assert invoke() == 0
    assert calls == [("actor0", 8), ("actor0", 24)]
    assert json.loads((logs / "actor0.status.json").read_text())["status"] == "PASS"
    assert "actor0\tPASS\t" in (logs / "summary.tsv").read_text()


def test_nonmemory_abort_is_not_retried(run_fixture):
    logs, calls, outcomes, invoke = run_fixture
    outcomes.append((-6, "Assertion failed", "partial"))
    assert invoke() == 1
    assert calls == [("actor0", 8)]
    assert json.loads((logs / "actor0.status.json").read_text())["status"] == "SYNTHESIS_ERROR"


def test_zero_exit_without_completion_is_not_pass(run_fixture):
    logs, calls, outcomes, invoke = run_fixture
    outcomes.append((0, "", "partial log"))
    assert invoke() == 1
    assert not (logs / "actor0.sha256").exists()
    assert "actor0\tSYNTHESIS_ERROR\t" in (logs / "summary.tsv").read_text()


def test_persistent_summary_error_stops_new_work_and_retains_actor_journal(
    run_fixture, monkeypatch
):
    logs, calls, outcomes, invoke = run_fixture
    original = runner.atomic_write
    summaries = []

    def atomic(path, text, **kwargs):
        if path.name == "summary.tsv":
            summaries.append(text)
            if len(summaries) > 1:
                raise OSError(errno.EIO, "persistent summary write failure")
        return original(path, text, **kwargs)

    monkeypatch.setattr(runner, "atomic_write", atomic)
    outcomes.append((0, "", "End of script\n"))
    assert invoke(("actor0", "actor1")) == 2
    assert calls == [("actor0", 8)]
    assert json.loads((logs / "actor0.status.json").read_text())["status"] == "PASS"


@pytest.mark.parametrize(
    "signature,limit,expected_calls",
    [
        ("current", 8, [("actor0", 24)]),
        ("current", 24, []),
        ("stale", 24, [("actor0", 8)]),
    ],
)
def test_resume_skips_only_matching_failed_limits(run_fixture, signature, limit, expected_calls):
    logs, calls, outcomes, invoke = run_fixture
    (logs / "actor0.status.json").write_text(
        json.dumps(
            {
                "signature": signature,
                "status": "MEMORY_FINAL",
                "virtual_memory_gib": limit,
            }
        )
    )
    outcomes.extend([(0, "", "End of script\n")] * len(expected_calls))
    assert invoke() == (0 if expected_calls else 1)
    assert calls == expected_calls


def test_no_resume_retries_even_known_final_memory_failure(run_fixture):
    logs, calls, outcomes, invoke = run_fixture
    (logs / "actor0.status.json").write_text(
        json.dumps(
            {
                "signature": "current",
                "status": "MEMORY_FINAL",
                "virtual_memory_gib": 24,
            }
        )
    )
    outcomes.append((0, "", "End of script\n"))
    assert invoke(extra=("--no-resume",)) == 0
    assert calls == [("actor0", 8)]
