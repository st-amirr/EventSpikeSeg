export DESIGN_NAME = convolution_plif_actor
export PLATFORM = asap7

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = $(wildcard $(PROJECT_DIR)/asic/rtl/*.sv)
export SDC_FILE = $(CONFIG_DIR)/orfs_asap7_constraint.sdc

export CLOCK_PORT = clk
export CLOCK_PERIOD = 5.0
export CORE_UTILIZATION = 35
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 2
export PLACE_DENSITY = 0.60

# This configuration is deliberately a small integrated actor prototype. Full-model PPA
# is invalid until actor-local state arrays are mapped to characterized SRAM macros.
