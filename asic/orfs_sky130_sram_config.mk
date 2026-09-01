export DESIGN_NAME = convolution_plif_actor
export PLATFORM = sky130hd
export FLOW_VARIANT = sram4x4

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)
SKY130_SRAM_DIR := $(CURDIR)/platforms/sky130ram/sky130_sram_1rw1r_80x64_8

export VERILOG_FILES = $(wildcard $(PROJECT_DIR)/asic/rtl/*.sv)
export VERILOG_DEFINES += -D EVENTSPIKESEG_EXTERNAL_SRAM_MACRO
export SDC_FILE = $(CONFIG_DIR)/orfs_sky130_sram_constraint.sdc
export PDN_TCL = $(CONFIG_DIR)/orfs_sky130_sram_pdn.tcl
export VERILOG_TOP_PARAMS = OUTPUT_WIDTH 4 OUTPUT_HEIGHT 4 DEST_COUNT 16 ADDRESS_WIDTH 4 USE_STATE_MACRO 1

export ADDITIONAL_LEFS = $(SKY130_SRAM_DIR)/sky130_sram_1rw1r_80x64_8.lef
export ADDITIONAL_LIBS = $(SKY130_SRAM_DIR)/sky130_sram_1rw1r_80x64_8_TT_1p8V_25C.lib
export ADDITIONAL_GDS = $(SKY130_SRAM_DIR)/sky130_sram_1rw1r_80x64_8.gds

export CLOCK_PORT = clk
export CLOCK_PERIOD = 20
export CORE_UTILIZATION = 25
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 20
export PLACE_DENSITY = 0.55
export MACRO_PLACE_HALO = 5 5
export MACRO_PLACE_CHANNEL = 10 10

# The amd64 OpenROAD image reproducibly receives SIGILL in post-CTS
# repair_timing under Apple-silicon emulation.  Keep CTS itself enabled, but
# rerun without this exploration-only switch on native x86 before signoff.
export SKIP_CTS_REPAIR_TIMING = 1

# This is a manufacturable actor-tile SRAM integration check, not a full-chip
# scaling result. Full-model capacity still depends on complete DSEC activity.
