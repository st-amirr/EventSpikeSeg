# Bugs and limitations

## Dataset representation limitation

The Ev-SegNet semantic download contains six aggregate event-statistic channels rather than raw asynchronous events. This limits direct claims about temporal sparsity and event-addressed FPGA execution. Raw-event validation requires original DDD17 recordings aligned to the semantic labels.

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

The new contenders span approximately 21k to 107k trainable parameters. Parameter count is only a proxy for FPGA cost; 5×5 kernels, wider pointwise layers, fourth-stage membrane state, event additions, memory banking, and line buffering must be measured/estimated separately before hardware selection.

## Open: continuous learned neuron parameters

PLIF beta, base threshold, inhibition strength, threshold-adaptation strength, and adaptation duration are still floating-point training variables. They require quantization and integer-reference regression before FPGA claims.
