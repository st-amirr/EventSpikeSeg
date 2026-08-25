#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${ASIC_BUILD_DIR:-${TMPDIR:-/tmp}/eventspikeseg-asic-check}"

mkdir -p "${BUILD_DIR}"

tops=(
  plif_update
  presynaptic_tap_array
  asynchronous_plif_actor
  convolution_plif_actor
  peer_membrane_inhibition
  triangular_threshold_adaptation
  class_argmax
  class_current_update
)

for top in "${tops[@]}"; do
  iverilog -g2012 -s "${top}" -o "${BUILD_DIR}/${top}.vvp" \
    "${PROJECT_DIR}"/asic/rtl/*.sv
done

printf 'Compiled %d SystemVerilog ASIC tops into %s\n' "${#tops[@]}" "${BUILD_DIR}"
