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
  event_fork2
  event_join2
  binary_event_union2
  event_channel_offset
  event_upsample2x
  channelized_convolution_scatter
  channelized_convolution_plif_actor
  streaming_channelized_plif_actor
  temporal_class_readout
  plif_leak_charge
  retinotopic_mechanism_update
  retinotopic_asynchronous_plif_actor
  actor_local_state_sram
)

for top in "${tops[@]}"; do
  if [[ "${top}" == "temporal_class_readout" ]]; then
    iverilog -g2012 -s "${top}" \
      -Ptemporal_class_readout.OUTPUT_WIDTH=2 \
      -Ptemporal_class_readout.OUTPUT_HEIGHT=2 \
      -Ptemporal_class_readout.INPUT_CHANNELS=2 \
      -Ptemporal_class_readout.CLASS_COUNT=3 \
      -o "${BUILD_DIR}/${top}.vvp" "${PROJECT_DIR}"/asic/rtl/*.sv
  elif [[ "${top}" == "retinotopic_asynchronous_plif_actor" ]]; then
    iverilog -g2012 -s "${top}" \
      -Pretinotopic_asynchronous_plif_actor.CHANNEL_COUNT=2 \
      -Pretinotopic_asynchronous_plif_actor.SPATIAL_DEST_COUNT=4 \
      -o "${BUILD_DIR}/${top}.vvp" "${PROJECT_DIR}"/asic/rtl/*.sv
  else
    iverilog -g2012 -s "${top}" -o "${BUILD_DIR}/${top}.vvp" \
      "${PROJECT_DIR}"/asic/rtl/*.sv
  fi
done

iverilog -g2012 -DEVENTSPIKESEG_EXTERNAL_SRAM_MACRO \
  -s convolution_plif_actor \
  -Pconvolution_plif_actor.OUTPUT_WIDTH=4 \
  -Pconvolution_plif_actor.OUTPUT_HEIGHT=4 \
  -Pconvolution_plif_actor.DEST_COUNT=16 \
  -Pconvolution_plif_actor.ADDRESS_WIDTH=4 \
  -Pconvolution_plif_actor.USE_STATE_MACRO=1 \
  -o "${BUILD_DIR}/convolution_plif_actor_sky130_macro.vvp" \
  "${PROJECT_DIR}"/asic/rtl/*.sv

printf 'Compiled %d SystemVerilog ASIC tops plus the external-SRAM actor into %s\n' \
  "${#tops[@]}" "${BUILD_DIR}"
