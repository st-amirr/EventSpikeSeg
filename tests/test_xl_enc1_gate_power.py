from pathlib import Path

import pytest

from scripts.prepare_xl_enc1_gate_power import (
    require_passing_rtl_results,
    validate_power,
    validate_sdf,
    validate_simulation,
)


def test_gate_sim_validation_requires_pass_and_clean_outputs(tmp_path: Path) -> None:
    log = tmp_path / "sim.log"
    vcd = tmp_path / "gate.vcd"
    log.write_text("GATE_REPLAY_PASS vectors=10 cycles=42\n", encoding="utf-8")
    vcd.write_text("$date\n$end\n", encoding="utf-8")
    assert validate_simulation(log, vcd)["vectors"] == 10
    log.write_text("GATE_REPLAY_PASS vectors=10\nFATAL X/Z\n", encoding="utf-8")
    with pytest.raises(ValueError, match="failure indicators"):
        validate_simulation(log, vcd)


def test_activity_power_validation_is_scoped(tmp_path: Path) -> None:
    log = tmp_path / "power.log"
    report = tmp_path / "power.rpt"
    annotation = tmp_path / "annotation.rpt"
    log.write_text("ACTIVITY_POWER_PASS\n", encoding="utf-8")
    report.write_text("Total 1.0 2.0 3.0\n", encoding="utf-8")
    annotation.write_text("Annotated pins: 99.5%\n", encoding="utf-8")
    result = validate_power(log, report, annotation)
    assert result["scope"].endswith("enc1_depthwise_partition")


def test_sdf_validation_checks_identity_and_cells(tmp_path: Path) -> None:
    log = tmp_path / "sdf.log"
    sdf = tmp_path / "design.sdf"
    log.write_text("SDF_GENERATION_PASS\n", encoding="utf-8")
    sdf.write_text(
        '(DELAYFILE\n (DESIGN "resident_actor_tile_pnr_top")\n'
        " (TIMESCALE 1ps)\n (CELL\n )\n (CELL\n )\n)\n",
        encoding="utf-8",
    )
    assert validate_sdf(log, sdf)["cell_records"] == 2


def test_gate_flow_requires_passing_rtl_junit(tmp_path: Path) -> None:
    results = tmp_path / "results.xml"
    results.write_text(
        '<testsuites><testsuite><testcase name="rtl"/></testsuite></testsuites>',
        encoding="utf-8",
    )
    require_passing_rtl_results(results)
    results.write_text(
        '<testsuites><testsuite><testcase name="rtl"><failure/></testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="RTL replay must pass"):
        require_passing_rtl_results(results)


def test_activity_power_validation_rejects_missing_total(tmp_path: Path) -> None:
    log = tmp_path / "power.log"
    report = tmp_path / "power.rpt"
    annotation = tmp_path / "annotation.rpt"
    log.write_text("ACTIVITY_POWER_PASS\n", encoding="utf-8")
    report.write_text("no aggregate row\n", encoding="utf-8")
    annotation.write_text("Annotated pins: 99.5%\n", encoding="utf-8")
    with pytest.raises(ValueError, match="total"):
        validate_power(log, report, annotation)


def test_activity_power_validation_rejects_low_coverage(tmp_path: Path) -> None:
    log = tmp_path / "power.log"
    report = tmp_path / "power.rpt"
    annotation = tmp_path / "annotation.rpt"
    log.write_text("ACTIVITY_POWER_PASS\n", encoding="utf-8")
    report.write_text("Total 1.0\n", encoding="utf-8")
    annotation.write_text("Annotated pins: 82.0%\n", encoding="utf-8")
    with pytest.raises(ValueError, match="too low"):
        validate_power(log, report, annotation)


def test_activity_power_validation_accepts_opensta_pin_counts(tmp_path: Path) -> None:
    log = tmp_path / "power.log"
    report = tmp_path / "power.rpt"
    annotation = tmp_path / "annotation.rpt"
    log.write_text("ACTIVITY_POWER_PASS\n", encoding="utf-8")
    report.write_text("Total 0.1\n", encoding="utf-8")
    annotation.write_text("vcd 372491\nunannotated 0\n", encoding="utf-8")
    result = validate_power(log, report, annotation)
    assert result["minimum_annotation_percent"] == 100.0
