#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ -z "${ORFS_ROOT:-}" ]]; then
  printf 'ORFS_ROOT must point to an OpenROAD-flow-scripts checkout.\n' >&2
  exit 2
fi

bash "${SCRIPT_DIR}/check_rtl.sh"

make -C "${ORFS_ROOT}/flow" \
  DESIGN_CONFIG="${PROJECT_DIR}/asic/orfs_asap7_config.mk"
