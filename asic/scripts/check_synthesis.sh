#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if ! command -v yosys >/dev/null 2>&1; then
  printf 'Yosys is required for the local synthesis gate.\n' >&2
  exit 1
fi

cd "${PROJECT_DIR}"

yosys -q -p '
  read_verilog -sv asic/rtl/plif_update.sv asic/rtl/asynchronous_plif_actor.sv;
  hierarchy -top asynchronous_plif_actor;
  proc; memory; opt; check
'

yosys -q -p '
  read_verilog -sv asic/rtl/channelized_convolution_scatter.sv;
  hierarchy -top channelized_convolution_scatter;
  proc; opt; check
'

yosys -q -p '
  read_verilog -sv asic/rtl/plif_leak_charge.sv
    asic/rtl/retinotopic_mechanism_update.sv;
  hierarchy -top retinotopic_mechanism_update;
  proc; memory; opt; check
'

yosys -q -p '
  read_verilog -sv asic/rtl/actor_local_state_sram.sv;
  hierarchy -top actor_local_state_sram;
  proc; memory; opt; check
'

# Keep this representative readout instance deliberately small. The production
# state arrays must be replaced by characterized compiled SRAM before full-chip
# synthesis is a meaningful physical-design or PPA experiment.
yosys -q -p '
  read_verilog -sv asic/rtl/temporal_class_readout.sv;
  chparam -set OUTPUT_WIDTH 2 -set OUTPUT_HEIGHT 2
    -set INPUT_CHANNELS 2 -set CLASS_COUNT 3 temporal_class_readout;
  hierarchy -top temporal_class_readout;
  proc; memory; opt; check
'

printf 'Representative SystemVerilog synthesis checks passed.\n'
