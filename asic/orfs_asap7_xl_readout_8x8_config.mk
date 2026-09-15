export DESIGN_NAME = resident_readout_tile_pnr_top
export PLATFORM = asap7
export FLOW_VARIANT = xl_readout_8x8

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = \
  $(PROJECT_DIR)/asic/rtl/resident_temporal_class_readout.sv \
  $(PROJECT_DIR)/artifacts/ASIC_XL/full_chip_layout/readout_8x8_tile.sv
export SDC_FILE = $(CONFIG_DIR)/orfs_asap7_resident_readout_tile_constraint.sdc

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

# This hard master contains every class-current register for one exact 8x8
# spatial readout tile. Full XL integration requires 4,400 instances.
