#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

docker compose -f "${PROJECT_DIR}/compose_ASIC.yaml" run --rm rtl \
  python scripts/generate_resident_tile_pnr_top.py \
  artifacts/ASIC/model_spec.yaml \
  artifacts/ASIC/PPA/resident_detail_stem_2x2.sv \
  --actor detail_stem --tile-width 2 --tile-height 2

export ORFS_DESIGN_CONFIG="${PROJECT_DIR}/asic/orfs_asap7_resident_tile_config.mk"
export ORFS_REPORT_PLATFORM=asap7
export ORFS_REPORT_DESIGN=resident_actor_tile_pnr_top
export ORFS_REPORT_VARIANT=resident_detail_stem_2x2
export ORFS_REPORT_TIME_UNIT=ps
exec bash "${SCRIPT_DIR}/run_orfs.sh"
