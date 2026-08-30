#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if ! command -v yosys >/dev/null 2>&1; then
  printf 'Yosys is required for the local synthesis gate.\n' >&2
  exit 1
fi

cd "${PROJECT_DIR}"

printf 'Synthesizing asynchronous PLIF actor...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/plif_update.sv asic/rtl/asynchronous_plif_actor.sv;
  hierarchy -top asynchronous_plif_actor;
  proc; memory; opt; check
'

printf 'Synthesizing SRAM-backed asynchronous PLIF actor control...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/plif_update.sv asic/rtl/asynchronous_plif_actor_sram.sv;
  hierarchy -top asynchronous_plif_actor_sram;
  proc; memory; opt; check
'

printf 'Synthesizing channelized convolution scatter...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/channelized_convolution_scatter.sv;
  hierarchy -top channelized_convolution_scatter;
  proc; opt; check
'

printf 'Synthesizing retinotopic mechanism commit...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/plif_leak_charge.sv asic/rtl/retinotopic_mechanism_update.sv;
  hierarchy -top retinotopic_mechanism_update;
  proc; memory; opt; check
'

printf 'Synthesizing SRAM-backed retinotopic actor control...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/plif_leak_charge.sv asic/rtl/retinotopic_mechanism_update.sv asic/rtl/retinotopic_asynchronous_plif_actor_sram.sv;
  hierarchy -top retinotopic_asynchronous_plif_actor_sram -chparam CHANNEL_COUNT 2 -chparam SPATIAL_DEST_COUNT 4;
  proc; memory; opt; check
'

printf 'Synthesizing actor-local SRAM boundary...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv;
  hierarchy -top actor_local_state_sram;
  proc; memory; opt; check
'

# Synthesize the readout arithmetic independently. The production per-pixel
# temporal score bank must use characterized compiled SRAM before full-chip
# synthesis is a meaningful physical-design or PPA experiment.
printf 'Synthesizing signed class-current readout datapath...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/class_current_update.sv;
  hierarchy -top class_current_update;
  proc; opt; check
'

printf 'Synthesizing SRAM-backed temporal readout control...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/temporal_class_readout_sram.sv;
  hierarchy -top temporal_class_readout_sram -chparam OUTPUT_WIDTH 2 -chparam OUTPUT_HEIGHT 2 -chparam INPUT_CHANNELS 2 -chparam CLASS_COUNT 3;
  proc; memory; opt; check
'

printf 'Synthesizing SRAM-backed residual union control...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/binary_event_union2_sram.sv;
  hierarchy -top binary_event_union2_sram -chparam OUTPUT_WIDTH 4 -chparam OUTPUT_HEIGHT 4 -chparam CHANNEL_COUNT 2 -chparam MAX_EVENTS 8;
  proc; memory; opt; check
'

printf 'Representative SystemVerilog synthesis checks passed.\n'
