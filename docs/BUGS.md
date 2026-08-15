# Bugs and limitations

## Dataset representation limitation

**Status: partially resolved in software.**

The Ev-SegNet download contains aggregate six-channel interval statistics rather than raw asynchronous event tuples. `event-bins` uses consecutive intervals and extracts only the two polarity histograms; `sequential-6ch` keeps all statistics. No HDF5 is required, and exact within-interval timing cannot be reconstructed.

## Rare-class collapse

**Status:** open.

Object, nature, human, and vehicle classes remain weak or absent in the low-budget mechanism screen. Ground-truth support for the 128-sample held-out subset was:

```text
flat               54,829 pixels
construction+sky  388,044
object               1,615
nature              50,690
human                  702
vehicle              28,408
```

The mechanism-screen winner predicted no nature or vehicle pixels and only one human pixel. This cannot be fixed by architecture ranking alone. Continue recording ground-truth and predicted pixel counts, and do not promote a model solely on overall pixel accuracy.

## Resolved: whole-feature-map binary homeostasis

The old `amax` activity rule treated one spike like dense activity and could raise an entire feature-map threshold. The active mechanism uses local triangular threshold adaptation driven by retinotopic membrane energy instead.

## Resolved: hidden hard winner gating in the active top five

The completed mechanism screen showed `winner_peer` inhibition starving the encoder: spike rates fell to approximately `0.0474 → 0.00306 → 0.000149` across enc1/enc2/enc3. The active structural top five therefore use `peer_membrane` inhibition only in the stem. The stronger winner gate remains a reusable component but is not part of the current contenders.

## Open: structural-cost trade-off

The historical structural contenders span approximately 21k to 107k trainable parameters; the canonical model is now 237,597 parameters. Parameter count is only a proxy for FPGA cost; 5×5 kernels, wider pointwise layers, fourth-stage membrane state, event additions, memory banking, and line buffering must be measured/estimated separately before hardware selection.

## Open: continuous learned neuron parameters

PLIF beta, base threshold, inhibition strength, threshold-adaptation strength, and adaptation duration are still floating-point training variables. They require quantization and integer-reference regression before FPGA claims.


## Open: native-resolution CPU BPTT memory

Native-resolution DDD17 training with full BPTT over `T=15` retains high-resolution PLIF/convolution autograd state across many layers. This can exceed 32 GB of system RAM even though model parameters are small. Lossless fixes already applied include immediate per-batch graph/reference release, `set_to_none=True` gradient clearing, and skipping training-only auxiliary heads during evaluation. The old stride-0 repeated-input view was removed with temporal-v2. Activation checkpointing, lower precision, truncated BPTT, lower resolution, and shorter T are not enabled automatically because they trade compute or change the training calculation.


## 2026-08-09 — Native-resolution training memory root cause

Native-resolution batch-1 training exposed an avoidable full-resolution temporal-state cost on top of intrinsic T=15 BPTT. The final model now keeps triangular fLong off on the stem/x1/detail path and enables it from x2 onward, where spatial state is 4× smaller. Stateless convolution plus affine current transforms are vectorized over the combined T×N batch dimension while PLIF/LIF updates remain sequential, preserving identical temporal dynamics and gradients. Training returns scalar activity-rate diagnostics instead of retaining complete hidden TNCHW spike sequences solely for regularization.


## Resolved: fake temporal axis from repeated static input

**Status:** resolved in code on 2026-08-14.

Previously one six-channel Ev-SegNet sample was expanded across all `T` SNN updates. That made timestep sweeps primarily measure repeated membrane integration rather than chronological sensory context. The temporal-v2 loader forbids this behavior.

Regression coverage verifies that sequential timesteps contain distinct source frames and that temporal windows cannot cross sequence boundaries or frame-index gaps.

## Open: installed training event tensors are incomplete

**Status:** dataset installation issue detected automatically.

The installed `events/train` folder has 2,887 NumPy tensors while `labels/train` has 10,001 indexed masks. Only `rec1487339175_export` is represented in the active event manifest. This loss of recording diversity is a likely accuracy limiter and must be fixed at the dataset installation level; the loader reports the mismatch explicitly.
