from pathlib import Path

import pytest

from scripts.run_xl_actor_activity_vcd import assert_cocotb_results_passed


def _write_results(path: Path, testcase: str) -> None:
    path.write_text(
        f'<testsuites><testsuite><testcase name="trace">{testcase}</testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )


def test_cocotb_results_accept_a_passing_testcase(tmp_path: Path) -> None:
    results = tmp_path / "results.xml"
    _write_results(results, "")
    assert_cocotb_results_passed(results)


@pytest.mark.parametrize("outcome", ["<failure/>", "<error/>"])
def test_cocotb_results_reject_nonpassing_testcase(
    tmp_path: Path, outcome: str
) -> None:
    results = tmp_path / "results.xml"
    _write_results(results, outcome)
    with pytest.raises(RuntimeError, match="cocotb verification failed"):
        assert_cocotb_results_passed(results)


def test_cocotb_results_reject_missing_or_empty_suite(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="did not produce"):
        assert_cocotb_results_passed(tmp_path / "missing.xml")
    results = tmp_path / "results.xml"
    results.write_text("<testsuites/>", encoding="utf-8")
    with pytest.raises(RuntimeError, match="testcases=0"):
        assert_cocotb_results_passed(results)
