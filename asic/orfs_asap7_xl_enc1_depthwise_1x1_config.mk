export DESIGN_NAME = resident_actor_tile_pnr_top
export PLATFORM = asap7
export FLOW_VARIANT = xl_enc1_depthwise_1x1

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = \
  $(PROJECT_DIR)/asic/rtl/resident_convolution_synapses.sv \
  $(PROJECT_DIR)/asic/rtl/resident_plif_population.sv \
  $(PROJECT_DIR)/asic/rtl/retinotopic_mechanism_update.sv \
  $(PROJECT_DIR)/asic/rtl/resident_retinotopic_plif_population.sv \
  $(PROJECT_DIR)/asic/rtl/resident_channelized_plif_actor.sv \
  $(PROJECT_DIR)/asic/rtl/tiled_resident_channelized_plif_actor.sv \
  $(PROJECT_DIR)/artifacts/ASIC_XL/partitioned_synthesis_1x1/enc1_depthwise_tile.sv
export SDC_FILE = $(CONFIG_DIR)/orfs_asap7_resident_tile_constraint.sdc

export CLOCK_PORT = clk
export CLOCK_PERIOD = 5000
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 2
export PLACE_DENSITY = 0.60
export SKIP_CTS_REPAIR_TIMING = 1
export ADDER_MAP_FILE =
export SLEW_MARGIN = 50

export SYNTH_OPERATIONS_ARGS = -noalumacc
export ABC_AREA = 1

# Checkpoint-exact XL enc1 depthwise actor at one spatial coordinate. This is a
# per-partition physical characterization, not a full-chip PPA flow.
