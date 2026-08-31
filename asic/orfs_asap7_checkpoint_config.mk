export DESIGN_NAME = eventspikeseg140k_dag_top
export DESIGN_NICKNAME = eventspikeseg140k_checkpoint_reduced
export PLATFORM = asap7

CONFIG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_DIR := $(abspath $(CONFIG_DIR)/..)

export VERILOG_FILES = \
  $(wildcard $(PROJECT_DIR)/asic/rtl/*.sv) \
  $(PROJECT_DIR)/asic/tech/asap7/eventspikeseg_1rw_sram_macro.sv \
  $(PROJECT_DIR)/artifacts/asic_rtl_replay_smoke_v4_6class/eventspikeseg140k_replay_top.sv \
  $(PLATFORM_DIR)/verilog/fakeram_512x128.sv \
  $(PLATFORM_DIR)/verilog/fakeram_2048x128.sv
export VERILOG_DEFINES = -D EVENTSPIKESEG_EXTERNAL_SRAM_MACRO
# The builtin Yosys frontend repeatedly specializes this 25-actor parameterized
# DAG before synthesis. Slang elaborates the same SystemVerilog in one pass.
# Flat synthesis avoids ORFS's two-pass hierarchy cost; the physical SRAM cells
# remain Liberty-backed black boxes in either mode.
export SYNTH_HDL_FRONTEND = slang
export SYNTH_HIERARCHICAL = 0
export VERILOG_TOP_PARAMS = \
  USE_SCORE_SRAM_MACRO 1 \
  USE_RESIDUAL_SRAM_MACRO 1 \
  USE_ACTOR_STATE_SRAM_MACRO 1 \
  RESIDUAL_MAX_EVENTS 512

export ADDITIONAL_LEFS = \
  $(PLATFORM_DIR)/lef/fakeram_512x128.lef \
  $(PLATFORM_DIR)/lef/fakeram_2048x128.lef
export ADDITIONAL_LIBS = \
  $(PLATFORM_DIR)/lib/NLDM/fakeram_512x128.lib \
  $(PLATFORM_DIR)/lib/NLDM/fakeram_2048x128.lib

export SDC_FILE = $(CONFIG_DIR)/orfs_asap7_constraint.sdc
export CLOCK_PORT = clk
export CLOCK_PERIOD = 5.0
export CORE_UTILIZATION = 30
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export PLACE_DENSITY = 0.55

# This route contains the checkpoint's complete 25-actor logic, real weights,
# mechanisms, and topology at reduced spatial depth. Native SRAM area/power is
# recomposed from sram_manifest.json and the revision-pinned FakeRAM catalog.
