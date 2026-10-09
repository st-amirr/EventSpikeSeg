"""Measure the bounded SS/0C MOS geometry/bias grid for one event width."""

from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/test_sky130_ms_first_event_clamp.py"
GEOMETRIES = (0.5, 0.625, 0.75, 0.875, 1.0, 1.25, 1.5, 1.75, 2.0,
              2.5, 3.0, 3.5, 4.0)
BIAS_FRACTIONS = (0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)


def run_point(point: tuple[float, float, float]) -> tuple[float, float, int, str]:
    width_ns, geometry, fraction = point
    command = [sys.executable, str(SCRIPT), "--mos-corner=ss", "--temperature-c=0",
               f"--gate-fraction={fraction:g}", f"--injector-geometry-scale={geometry:g}",
               "--tight-solver", "--step-ns=0.1", f"--event-width-ns={width_ns:g}",
               "--post-event-delay-ns=20", "--gate-slew-ns=2",
               "--cases=before_10ns", "--shared-bank-load"]
    result = subprocess.run(command, capture_output=True, text=True,
                            cwd=ROOT, timeout=180)
    if result.returncode:
        return geometry, fraction, result.returncode, (result.stdout + result.stderr)[-1800:]
    return geometry, fraction, 0, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-width-ns", type=float, default=42.2657)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.event_width_ns <= 0 or not 1 <= args.workers <= 4:
        parser.error("event width must be positive and workers must be 1..4")
    points = [(args.event_width_ns, geometry, fraction)
              for fraction in BIAS_FRACTIONS for geometry in GEOMETRIES]
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_point, point) for point in points]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            geometry, fraction, return_code, output = future.result()
            print(f"[{completed}/{len(points)}] bias={fraction:g} geometry={geometry:g} "
                  f"{'ok' if return_code == 0 else f'FAILED({return_code})'}", flush=True)
            if return_code:
                failures.append((geometry, fraction, output))
    if failures:
        for geometry, fraction, output in failures:
            print(f"\n--- failure bias={fraction:g}, geometry={geometry:g} ---\n{output}")
        return 1
    print(f"Completed {len(points)} geometry/bias measurements at {args.event_width_ns:g} ns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
