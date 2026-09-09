#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

docker run --rm --platform linux/amd64 \
  --workdir /workspace \
  --env PYTHONPATH=/workspace/src \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  --volume "${PROJECT_DIR}/artifacts:/workspace/artifacts" \
  "${ASIC_CPU_IMAGE:-eventspikeseg:torch2.2.2-cpu-verification}" \
  python scripts/generate_resident_tile_pnr_top.py \
  artifacts/ASIC/model_spec.yaml \
  artifacts/ASIC/PPA/resident_detail_stem_q7_16_acc32_2x2x2.sv \
  --actor detail_stem --tile-width 2 --tile-height 2 --tile-columns 2

export ORFS_DESIGN_CONFIG="${PROJECT_DIR}/asic/orfs_asap7_resident_two_tile_config.mk"
export ORFS_REPORT_PLATFORM=asap7
export ORFS_REPORT_DESIGN=resident_actor_tile_pnr_top
export ORFS_REPORT_VARIANT=resident_detail_stem_q7_16_acc32_2x2x2
export ORFS_REPORT_TIME_UNIT=ps
exec bash "${SCRIPT_DIR}/run_orfs.sh"
