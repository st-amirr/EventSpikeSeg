export DESIGN_NAME = convolution_plif_actor
export PLATFORM = asap7
export FLOW_VARIANT = logic4x4

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = $(wildcard $(PROJECT_DIR)/asic/rtl/*.sv)
export SDC_FILE = $(CONFIG_DIR)/orfs_asap7_constraint.sdc

# ASAP7 has no characterized SRAM in the public ORFS platform. Keep this
# standard-cell-only run small enough to characterize actor control/datapath
# logic without pretending that expanded registers represent the ASIC SRAMs.
export VERILOG_TOP_PARAMS = OUTPUT_WIDTH 4 OUTPUT_HEIGHT 4 DEST_COUNT 16 ADDRESS_WIDTH 4

export CLOCK_PORT = clk
export CLOCK_PERIOD = 5000
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 2
export PLACE_DENSITY = 0.60

# ORFS documents this switch for architectural exploration/CI. The amd64
# OpenROAD binary reproducibly receives SIGILL under Apple-silicon emulation
# inside post-CTS repair_timing; native x86 characterization should re-enable it.
export SKIP_CTS_REPAIR_TIMING = 1

# This configuration is deliberately a small integrated actor prototype. Full-model PPA
# is invalid until actor-local state arrays are mapped to characterized SRAM macros.
