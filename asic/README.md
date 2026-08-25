# EventSpikeSeg ASIC flow

The hardware implementation is native synthesizable SystemVerilog. Icarus Verilog and
cocotb provide executable RTL checks, Yosys performs technology mapping, and OpenROAD
Flow Scripts (ORFS) performs floorplanning through routed layout, parasitic extraction,
timing, and power analysis.

## Platform decision

- `asap7` is the primary open, reproducible **research PPA** platform. It is a predictive
  7 nm FinFET platform, not a manufacturable foundry PDK and not tapeout signoff.
- `sky130ram` is the future open, manufacturable **tile/test-chip** check when the actor
  state arrays have been replaced by explicit SRAM macros. It is not dense enough for
  the complete native-resolution state on one economical die.
- A complete manufacturable EventSpikeSeg chip requires an accessible 22/28 nm-or-better
  foundry PDK plus characterized high-density SRAM macros. That target cannot be called
  selected or power-signoff-ready until those libraries are available.

The distinction matters because 143,904 int8 synaptic weights consume only about
0.137 MiB, while the frozen 440x640 graph has 30,976,000 logical membranes. The current
exact dense reference is 189.60 MiB when int16 membrane, adaptation fields, and 24-bit
lazy-update tags are all included. Standard-cell flip-flops are not an acceptable
full-chip memory implementation.

## Current synthesis boundary

`convolution_plif_actor.sv` integrates the presynaptic convolution scatter with a local
PLIF population. Static kernel weights are elaboration-time constants, and the actor's
small default arrays make control/dataflow executable. The repository also contains
standalone PLIF, inhibition, adaptation, and readout blocks. Before full-chip PPA, the
behavioral state arrays must be replaced by actor-local SRAM macro wrappers with the same
logical ownership and no inter-layer state fetch.

Run native SystemVerilog compilation and the cocotb suite:

```sh
bash asic/scripts/check_rtl.sh
python scripts/run_rtl_tests.py
```

Set `ASIC_BUILD_DIR` to redirect generated netlists outside the repository when needed.

If an ORFS checkout or installation is available, set `ORFS_ROOT` to its root and run:

```sh
ORFS_ROOT=/path/to/OpenROAD-flow-scripts bash asic/scripts/run_orfs.sh
```

The ORFS configuration targets the integrated convolution/PLIF actor prototype on ASAP7.
Its report is a representative actor result, not a 25-actor full-model estimate. Activity-based power
requires a representative VCD/SAIF from the exported DSEC event stream; vectorless
default-toggle power must be labeled preliminary.
