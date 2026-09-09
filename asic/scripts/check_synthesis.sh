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
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/initialized_actor_state_bank.sv asic/rtl/plif_update.sv asic/rtl/asynchronous_plif_actor.sv;
  hierarchy -top asynchronous_plif_actor;
  proc; memory; opt; check
'

printf 'Synthesizing channelized convolution scatter...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/channelized_convolution_scatter.sv;
  hierarchy -top channelized_convolution_scatter;
  proc; opt; check
'

printf 'Synthesizing presynaptic tap projection...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/presynaptic_tap_array.sv;
  hierarchy -top presynaptic_tap_array;
  proc; opt; check
'

printf 'Synthesizing retinotopic mechanism commit...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/plif_leak_charge.sv asic/rtl/retinotopic_mechanism_update.sv;
  hierarchy -top retinotopic_mechanism_update;
  proc; memory; opt; check
'

printf 'Synthesizing the direct resident convolution/PLIF actor...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/resident_convolution_synapses.sv asic/rtl/resident_plif_population.sv asic/rtl/retinotopic_mechanism_update.sv asic/rtl/resident_retinotopic_plif_population.sv asic/rtl/resident_channelized_plif_actor.sv;
  chparam -set INPUT_CHANNELS 1 -set OUTPUT_CHANNELS 2 -set INPUT_WIDTH 2 -set INPUT_HEIGHT 1 -set OUTPUT_WIDTH 2 -set OUTPUT_HEIGHT 1 -set KERNEL_WIDTH 1 -set KERNEL_HEIGHT 1 -set PAD_X 0 -set PAD_Y 0 -set KERNEL_WEIGHTS 1542 -set CHANNEL_BETAS 2147450879 -set CHANNEL_THRESHOLDS 655370 resident_channelized_plif_actor;
  hierarchy -top resident_channelized_plif_actor;
  proc; memory; opt; check
'

printf 'Synthesizing the receptive-halo resident tile hierarchy...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/resident_convolution_synapses.sv asic/rtl/resident_plif_population.sv asic/rtl/retinotopic_mechanism_update.sv asic/rtl/resident_retinotopic_plif_population.sv asic/rtl/resident_channelized_plif_actor.sv asic/rtl/tiled_resident_channelized_plif_actor.sv;
  chparam -set INPUT_CHANNELS 1 -set OUTPUT_CHANNELS 1 -set INPUT_WIDTH 4 -set INPUT_HEIGHT 2 -set OUTPUT_WIDTH 4 -set OUTPUT_HEIGHT 2 -set TILE_WIDTH 2 -set TILE_HEIGHT 2 -set KERNEL_WIDTH 3 -set KERNEL_HEIGHT 3 -set PAD_X 1 -set PAD_Y 1 tiled_resident_channelized_plif_actor;
  hierarchy -top tiled_resident_channelized_plif_actor;
  proc; memory; opt; check
'

printf 'Synthesizing actor-local SRAM boundary...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/initialized_actor_state_bank.sv;
  hierarchy -top initialized_actor_state_bank;
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

printf 'Synthesizing resident temporal class readout...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/resident_temporal_class_readout.sv;
  chparam -set INPUT_CHANNELS 2 -set CLASS_COUNT 3 -set OUTPUT_WIDTH 2 -set OUTPUT_HEIGHT 1 -set PREDICTION_BINS 2 -set READOUT_WEIGHTS 281470715297793 resident_temporal_class_readout;
  hierarchy -top resident_temporal_class_readout;
  proc; memory; opt; check
'

printf 'Synthesizing SRAM-backed temporal readout control...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/initialized_actor_state_bank.sv asic/rtl/temporal_class_readout.sv;
  chparam -set OUTPUT_WIDTH 2 -set OUTPUT_HEIGHT 2 -set INPUT_CHANNELS 2 -set CLASS_COUNT 3 temporal_class_readout;
  hierarchy -top temporal_class_readout;
  proc; memory; opt; check
'

printf 'Synthesizing XL spike-mask attention primitive...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/resident_spike_mask_attention.sv;
  chparam -set HEADS 2 -set HEAD_DIM 2 -set SPATIAL_COUNT 2 resident_spike_mask_attention;
  hierarchy -top resident_spike_mask_attention;
  proc; opt; check
'

printf 'Synthesizing SRAM-backed residual union...\n'
yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv asic/rtl/binary_event_union2.sv;
  hierarchy -top binary_event_union2;
  proc; memory; opt; check
'

printf 'Synthesizing the external-SRAM convolution/PLIF actor boundary...\n'
yosys -q -p '
  read_verilog -sv -DSYNTHESIS -DEVENTSPIKESEG_EXTERNAL_SRAM_MACRO asic/rtl/*.sv;
  chparam -set OUTPUT_WIDTH 4 -set OUTPUT_HEIGHT 4 -set DEST_COUNT 16 -set ADDRESS_WIDTH 4 -set USE_STATE_MACRO 1 convolution_plif_actor;
  hierarchy -top convolution_plif_actor;
  proc; memory; opt; check
'

printf 'Representative SystemVerilog synthesis checks passed.\n'
