export DESIGN_NAME = xl_hm_readout__out_4x4
export PLATFORM = asap7
export FLOW_VARIANT = hard_macro_exact

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = \
  $(PROJECT_DIR)/asic/rtl/resident_temporal_class_readout.sv \
  $(PROJECT_DIR)/artifacts/ASIC_XL/hard_hierarchy/masters/xl_hm_readout__out_4x4/xl_hm_readout__out_4x4.sv
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

# This hard master contains every class-current register for one exact 4x4
# spatial readout tile. Full XL integration requires 17,600 submacro
# instances grouped as 4,400 nominal 8x8 tiles.
