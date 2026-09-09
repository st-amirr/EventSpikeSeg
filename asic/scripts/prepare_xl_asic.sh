#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CHECKPOINT="${XL_CHECKPOINT:-artifacts/model_checkpoints/dsec_XL/EventSpikeSegXL_seed17_epoch001.pt}"
EXPORT_DIR="${XL_ASIC_EXPORT:-artifacts/ASIC_XL}"

cd "${PROJECT_DIR}"
python scripts/export_asic_model.py --checkpoint "${CHECKPOINT}" --output "${EXPORT_DIR}"
python scripts/generate_asic_top.py \
  "${EXPORT_DIR}/model_spec.yaml" \
  "${EXPORT_DIR}/generated_eventspikesegxl_dag_top.sv" \
  --module-name eventspikesegxl_dag_top --architecture resident \
  --resident-tile-width 8 --resident-tile-height 8
python scripts/plan_asic_resident_tiles.py \
  "${EXPORT_DIR}/model_spec.yaml" "${EXPORT_DIR}/resident_tile_plan.json"
python scripts/generate_sram_manifest.py \
  --export "${EXPORT_DIR}" --output "${EXPORT_DIR}/sram_manifest.json"

printf 'Prepared XL ASIC export and RTL in %s; synthesis was not run.\n' "${EXPORT_DIR}"
