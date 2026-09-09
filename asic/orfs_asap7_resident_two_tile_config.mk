export DESIGN_NAME = resident_actor_tile_pnr_top
export PLATFORM = asap7
export FLOW_VARIANT = resident_detail_stem_q7_16_acc32_2x2x2

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = \
  $(PROJECT_DIR)/asic/rtl/resident_convolution_synapses.sv \
  $(PROJECT_DIR)/asic/rtl/resident_plif_population.sv \
  $(PROJECT_DIR)/asic/rtl/retinotopic_mechanism_update.sv \
  $(PROJECT_DIR)/asic/rtl/resident_retinotopic_plif_population.sv \
  $(PROJECT_DIR)/asic/rtl/resident_channelized_plif_actor.sv \
  $(PROJECT_DIR)/asic/rtl/tiled_resident_channelized_plif_actor.sv \
  $(PROJECT_DIR)/artifacts/ASIC/PPA/resident_detail_stem_q7_16_acc32_2x2x2.sv
export SDC_FILE = $(CONFIG_DIR)/orfs_asap7_resident_tile_constraint.sdc

export CLOCK_PORT = clk
export CLOCK_PERIOD = 5000
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 2
export PLACE_DENSITY = 0.60
export SKIP_CTS_REPAIR_TIMING = 1
export ADDER_MAP_FILE =
# OpenROAD interprets this as an integer percentage, not a multiplier.
export SLEW_MARGIN = 50

# Checkpoint-exact Q7.16/int24-weight, Q15.16/int32-state 2x2 child tiles
# arranged in a 2x1 detail_stem boundary.
# This run measures hierarchy/fanout effects only; it is not full-chip PPA.
