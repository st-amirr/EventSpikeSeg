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
  asynchronous_plif_actor_sram
  convolution_plif_actor
  peer_membrane_inhibition
  triangular_threshold_adaptation
  class_argmax
  class_current_update
  event_fork2
  event_join2
  binary_event_union2
  binary_event_union2_sram
  event_channel_offset
  event_upsample2x
  channelized_convolution_scatter
  channelized_convolution_plif_actor
  streaming_channelized_plif_actor
  temporal_class_readout
  temporal_class_readout_sram
  plif_leak_charge
  retinotopic_mechanism_update
  retinotopic_asynchronous_plif_actor
  retinotopic_asynchronous_plif_actor_sram
  actor_local_state_sram
)

for top in "${tops[@]}"; do
  if [[ "${top}" == "temporal_class_readout" || "${top}" == "temporal_class_readout_sram" ]]; then
    iverilog -g2012 -s "${top}" \
      -P"${top}".OUTPUT_WIDTH=2 \
      -P"${top}".OUTPUT_HEIGHT=2 \
      -P"${top}".INPUT_CHANNELS=2 \
      -P"${top}".CLASS_COUNT=3 \
      -o "${BUILD_DIR}/${top}.vvp" "${PROJECT_DIR}"/asic/rtl/*.sv
  elif [[ "${top}" == "retinotopic_asynchronous_plif_actor" ||
          "${top}" == "retinotopic_asynchronous_plif_actor_sram" ]]; then
    iverilog -g2012 -s "${top}" \
      -P"${top}".CHANNEL_COUNT=2 \
      -P"${top}".SPATIAL_DEST_COUNT=4 \
      -o "${BUILD_DIR}/${top}.vvp" "${PROJECT_DIR}"/asic/rtl/*.sv
  else
    iverilog -g2012 -s "${top}" -o "${BUILD_DIR}/${top}.vvp" \
      "${PROJECT_DIR}"/asic/rtl/*.sv
  fi
done

printf 'Compiled %d SystemVerilog ASIC tops into %s\n' "${#tops[@]}" "${BUILD_DIR}"
