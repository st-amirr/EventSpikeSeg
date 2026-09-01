#!/usr/bin/env python3
"""Fail unless the routed ORFS actor prototype has clean extracted reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ZERO_METRICS = (
    "finish__timing__drv__max_slew",
    "finish__timing__drv__max_cap",
    "finish__timing__drv__max_fanout",
    "finish__timing__drv__setup_violation_count",
    "finish__timing__drv__hold_violation_count",
    "finish__flow__errors__count",
)


def check_reports(
    metrics_path: Path,
    drc_path: Path,
    *,
    time_unit: str = "ps",
    expected_macros: int | None = None,
) -> dict[str, float]:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    missing = [name for name in ZERO_METRICS if name not in metrics]
    if missing:
        raise RuntimeError(f"ORFS metrics are missing required checks: {missing}")
    failures = {
        name: float(metrics[name])
        for name in ZERO_METRICS
        if float(metrics[name]) != 0.0
    }
    if failures:
        raise RuntimeError(f"ORFS extracted checks are not clean: {failures}")
    if drc_path.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"ORFS detailed-route DRC report is not empty: {drc_path}")
    macro_count = int(metrics.get("finish__design__instance__count__class:macro", 0))
    if expected_macros is not None and macro_count != expected_macros:
        raise RuntimeError(
            f"ORFS macro count is {macro_count}, expected {expected_macros}"
        )
    time_to_ps = {"ps": 1.0, "ns": 1_000.0}[time_unit]
    return {
        "setup_slack_ps": float(metrics["finish__timing__setup__ws"]) * time_to_ps,
        "hold_slack_ps": float(metrics["finish__timing__hold__ws"]) * time_to_ps,
        "fmax_mhz": float(metrics["finish__timing__fmax"]) / 1e6,
        "macro_count": macro_count,
        "standard_cell_area_um2": float(metrics["finish__design__instance__area__stdcell"]),
        "vectorless_power_mw": float(metrics["finish__power__total"]) * 1e3,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("drc", type=Path)
    parser.add_argument("--time-unit", choices=("ps", "ns"), default="ps")
    parser.add_argument("--expected-macros", type=int)
    args = parser.parse_args()
    print(
        json.dumps(
            check_reports(
                args.metrics,
                args.drc,
                time_unit=args.time_unit,
                expected_macros=args.expected_macros,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
