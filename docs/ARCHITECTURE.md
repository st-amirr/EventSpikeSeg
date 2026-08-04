# EventSCNN-FPGA Architecture

EventSCNN-FPGA consumes timestamped `(t, x, y, polarity, batch)` events. Fixed-duration
binning produces the canonical integer-count tensor `[T, N, 2, 180, 240]`, with OFF
at channel 0 and ON at channel 1. Repeated events are repeated integer additions.

The software backbone is a SpikingJelly-compatible PyTorch model with three shared,
bias-free convolutions: `2→8, 5×5, stride 2`, `8→16, 3×3, stride 2`, and
`16→32, 3×3, stride 1`. Each is followed by the same explicit state transition:

1. `leaked = membrane - membrane / 2**beta_shift`
2. `candidate = leaked + convolution_current`
3. compare `candidate >= base_threshold + adaptive_threshold`
4. apply deterministic top-1 `f_inst` competition at each spatial position
5. subtract the effective threshold from winners and optionally decrement losers
6. emit winner spikes
7. update per-output-channel `f_long` adaptation from emitted spike counts

Integer division/shift semantics are specified separately in the fixed-point reference.
State is reset between independent sequences and retained within a tracking sequence.

The primary head is a bias-free 3×3 spiking pixel-attention convolution over Conv1,
producing `[T,N,1,90,120]`. Its weak training target contains event-active pixels inside
annotated boxes with local dilation; a filled rectangle is not the target. Predicted
attention is max/OR reduced to Conv3 resolution and weights spike-count classification.
At every timestep the resulting binary map gates Conv3 feature spikes. Their channel
counts drive bias-free class synapses followed by independent hardware-compatible LIF
output neurons. Classification is the deterministic argmax of emitted class-spike counts;
there is no analog linear/softmax readout in the learned inference path. Output class
neurons intentionally omit `f_inst` and `f_long`: lateral inhibition across mutually
exclusive class accumulators caused non-background spike starvation, while final argmax
already supplies decision competition. Tracking measures attention centroid and spread
and applies a deterministic single-target
alpha-beta update. Boxes remain training/evaluation metadata and may be derived from
attention for comparison metrics, but are not an inference ROI. The hardware reference
performs convolution by scattering shared-kernel additions from active spike addresses;
it never flattens convolution to a fully connected matrix.

Centroid moments, class argmax/confidence, and the alpha-beta tracker are deterministic
digital post-processing. They are intentionally not forced into artificial spiking
neurons; “fully spiking” here applies to the trainable feature, attention, and
classification path.

The canonical FPGA implementation language is VHDL-2008. Portable RTL unit verification
uses GHDL and cocotb. Existing FPGA-SNN frameworks, including Spiker+, may be reused or
adapted component-by-component only when they preserve the frozen arithmetic, sparse
shared-kernel architecture, and custom dynamics and reduce total integration risk.

## Planned FPGA memory hierarchy

The hardware backend will not use a BRAM-only policy. Its starting placement is hybrid:

- BRAM for the large, deep Conv1/Conv2/Conv3 membrane arrays;
- distributed LUTRAM for suitable small, frequently accessed memories such as the
  attention membrane, quantized shared weights, short event FIFOs, touched-address
  queues, accumulator tiles, and small lookup tables;
- registers for the two class-neuron states, per-channel homeostasis values, counters,
  and pipeline control.

This division is a design policy, not an implemented or synthesized result. Memory-port
replication, banking, packing waste, routing, and timing can make a nominal LUTRAM
candidate more expensive than BRAM. The final placement must therefore come from
side-by-side synthesis reports for the selected part while preserving the same widths,
addresses, arithmetic ordering, and golden outputs.

See `project_spec.yaml` for the complete contract and
`docs/exec-plans/active/project-bootstrap.md` for implementation status.

MEVDT sequence CSV timestamps are nanoseconds and are filtered at nanosecond precision
before conversion to relative microseconds. Detection rows are
`class x_min y_min x_max y_max`; only sub-micro-pixel floating-point border noise is
clipped. The official `data_splits/MEVDT_org_rate_{split}.csv` files define membership.
