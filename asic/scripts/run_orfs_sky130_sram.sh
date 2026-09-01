#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

export ORFS_DESIGN_CONFIG="${PROJECT_DIR}/asic/orfs_sky130_sram_config.mk"
export ORFS_REPORT_PLATFORM=sky130hd
export ORFS_REPORT_VARIANT=sram4x4
export ORFS_REPORT_TIME_UNIT=ns
export ORFS_EXPECTED_MACROS=2
exec bash "${SCRIPT_DIR}/run_orfs.sh"
