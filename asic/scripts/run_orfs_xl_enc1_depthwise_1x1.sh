#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TOP="${PROJECT_DIR}/artifacts/ASIC_XL/partitioned_synthesis_1x1/enc1_depthwise_tile.sv"

[[ -s "${TOP}" ]] || {
  printf "Missing synthesized XL top: %s\n" "${TOP}" >&2
  exit 2
}

export ORFS_DESIGN_CONFIG="${PROJECT_DIR}/asic/orfs_asap7_xl_enc1_depthwise_1x1_config.mk"
export ORFS_REPORT_PLATFORM=asap7
export ORFS_REPORT_DESIGN=resident_actor_tile_pnr_top
export ORFS_REPORT_VARIANT=xl_enc1_depthwise_1x1
export ORFS_REPORT_TIME_UNIT=ps
exec bash "${SCRIPT_DIR}/run_orfs.sh"
