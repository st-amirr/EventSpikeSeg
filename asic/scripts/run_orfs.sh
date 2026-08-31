#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ -z "${ORFS_ROOT:-}" ]]; then
  printf 'ORFS_ROOT must point to an OpenROAD-flow-scripts checkout.\n' >&2
  exit 2
fi

if [[ -f "${ORFS_ROOT}/env.sh" ]]; then
  # shellcheck disable=SC1091
  source "${ORFS_ROOT}/env.sh"
fi

WORK_HOME="${ASIC_ORFS_WORK_HOME:-${PROJECT_DIR}/artifacts/orfs_work}"
mkdir -p "${WORK_HOME}"
DESIGN_CONFIG="${ASIC_ORFS_DESIGN_CONFIG:-${PROJECT_DIR}/asic/orfs_asap7_config.mk}"
TARGET="${ASIC_ORFS_TARGET:-finish}"

if [[ -n "${ASIC_ORFS_WEIGHT_DIR:-}" ]]; then
  ln -sfn "${ASIC_ORFS_WEIGHT_DIR}" "${ORFS_ROOT}/flow/weights"
fi

make -C "${ORFS_ROOT}/flow" \
  WORK_HOME="${WORK_HOME}" \
  DESIGN_CONFIG="${DESIGN_CONFIG}" \
  "${TARGET}"
