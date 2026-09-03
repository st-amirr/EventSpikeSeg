#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

bash "${SCRIPT_DIR}/check_rtl.sh"

DESIGN_CONFIG="${ORFS_DESIGN_CONFIG:-${PROJECT_DIR}/asic/orfs_asap7_config.mk}"
REPORT_PLATFORM="${ORFS_REPORT_PLATFORM:-asap7}"
REPORT_DESIGN="${ORFS_REPORT_DESIGN:-convolution_plif_actor}"
REPORT_VARIANT="${ORFS_REPORT_VARIANT:-logic4x4}"
REPORT_TIME_UNIT="${ORFS_REPORT_TIME_UNIT:-ps}"

if [[ -n "${ORFS_ROOT:-}" ]]; then
  make -C "${ORFS_ROOT}/flow" \
    DESIGN_CONFIG="${DESIGN_CONFIG}"
  exit
fi

ORFS_IMAGE="${ORFS_IMAGE:-openroad/orfs:latest}"
OUTPUT_DIR="${PROJECT_DIR}/artifacts/OpenROAD"
mkdir -p \
  "${OUTPUT_DIR}/logs" \
  "${OUTPUT_DIR}/objects" \
  "${OUTPUT_DIR}/reports" \
  "${OUTPUT_DIR}/results"

docker run --rm --platform linux/amd64 \
  --volume "${PROJECT_DIR}:/workspace:ro" \
  --volume "${OUTPUT_DIR}/logs:/OpenROAD-flow-scripts/flow/logs" \
  --volume "${OUTPUT_DIR}/objects:/OpenROAD-flow-scripts/flow/objects" \
  --volume "${OUTPUT_DIR}/reports:/OpenROAD-flow-scripts/flow/reports" \
  --volume "${OUTPUT_DIR}/results:/OpenROAD-flow-scripts/flow/results" \
  "${ORFS_IMAGE}" \
  make -C /OpenROAD-flow-scripts/flow \
    DESIGN_CONFIG="/workspace/asic/$(basename "${DESIGN_CONFIG}")"

CHECK_ARGS=(
  "${OUTPUT_DIR}/logs/${REPORT_PLATFORM}/${REPORT_DESIGN}/${REPORT_VARIANT}/6_report.json"
  "${OUTPUT_DIR}/reports/${REPORT_PLATFORM}/${REPORT_DESIGN}/${REPORT_VARIANT}/5_route_drc.rpt"
  --time-unit "${REPORT_TIME_UNIT}"
)
if [[ -n "${ORFS_EXPECTED_MACROS:-}" ]]; then
  CHECK_ARGS+=(--expected-macros "${ORFS_EXPECTED_MACROS}")
fi
python3 "${SCRIPT_DIR}/check_orfs_reports.py" "${CHECK_ARGS[@]}"
