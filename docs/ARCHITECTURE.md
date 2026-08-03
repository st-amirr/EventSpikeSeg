# EventSCNN-FPGA Architecture

EventSCNN-FPGA consumes timestamped `(t, x, y, polarity, batch)` events. Fixed-duration
binning produces the canonical integer-count tensor `[T, N, 2, 180, 240]`, with OFF
at channel 0 and ON at channel 1. Repeated events are repeated integer additions.

The software backbone is a SpikingJelly-compatible PyTorch model with three shared,
bias-free convolutions: `2→8, 5×5, stride 2`, `8→16, 3×3, stride 2`, and
`16→32, 3×3, stride 2`. Each is followed by the same explicit state transition:

1. `leaked = membrane - membrane / 2**beta_shift`
2. `candidate = leaked + convolution_current`
3. compare `candidate >= base_threshold + adaptive_threshold`
4. apply deterministic top-1 `f_inst` competition at each spatial position
5. subtract the effective threshold from winners and optionally decrement losers
6. emit winner spikes
7. update per-output-channel `f_long` adaptation from emitted spike counts

Integer division/shift semantics are specified separately in the fixed-point reference.
State is reset between independent sequences and retained within a tracking sequence.

The proposal head forms a low-resolution objectness spike map and extracts connected
components. Classification uses ROI spike-count pooling. Tracking uses a deterministic
single-target alpha-beta state update. The hardware reference performs convolution by
scattering shared-kernel additions from active spike addresses; it never flattens a
convolution to a fully connected matrix.

The canonical FPGA implementation language is VHDL-2008. Portable RTL unit verification
uses GHDL and cocotb. Existing FPGA-SNN frameworks, including Spiker+, may be reused or
adapted component-by-component only when they preserve the frozen arithmetic, sparse
shared-kernel architecture, and custom dynamics and reduce total integration risk.

See `project_spec.yaml` for the complete contract and
`docs/exec-plans/active/project-bootstrap.md` for implementation status.
