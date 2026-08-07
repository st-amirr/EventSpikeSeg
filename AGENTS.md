# EventSpikeSeg-FPGA Agent Instructions

## Mission

Build a lightweight event-camera SNN for six-class DDD17 semantic segmentation, identify a strong spike-native architecture, then map the confirmed model to sparse fixed-point VHDL.

## Source-of-truth order

1. `project_spec.yaml`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. active ablation plan
6. tests and executable commands

## Model-file contract

```text
model.py              canonical architecture only
top_ten_models.py     frozen round-one definitions
top_five_models.py    preserved v1/v2 + active retinotopic-mechanism
model_components.py   shared tested primitives
```

Do not put experimental registries back into `model.py`.

## Current evidence

- incumbent: `v10_fpga_hybrid`, seed-17 mIoU 0.3130
- top-five v1 rejected; best 0.2464
- top-five v2 completed first three only:
  - `f01r_v10_plif_threshold`: 0.2821
  - `f02r_v10_plif_ratehomeo`: 0.2047
  - `f03r_v10_plif_grouped_inst`: 0.1967
- v2 indicates PLIF + learned threshold is substantially healthier than global rate homeostasis or grouped top-k competition.

## Retinotopic-mechanism contract

Source: Debat et al. (2021), *Event-Based Trajectory Prediction Using Spiking Neural Networks*.

Do not describe Debat et al. as using global firing-rate target homeostasis. Its mechanism is retinotopic and membrane-energy driven:

- `retinotopic_membrane_energy`: local RMS/mean-square membrane-energy term for neurons sharing one patch, accounting for threshold adaptation.
- `UInst = fInst * UPropInh`: instantaneous retinotopic inhibition; the source asynchronous mechanism prevents peers from spiking and reduces peer membrane potential.
- `UMaxThresh = fLong * UPropInh`.
- every `ULong` process rises linearly over `TThresh`, then falls linearly over another `TThresh`.
- active `ULong` processes from filters sharing the patch are summed into the local threshold penalty.
- custom parameters were tuned by a genetic algorithm, not learned by STDP.

Active current top-five design may use bounded learnable continuous analogues under surrogate-gradient training, but must keep the spatial/local mechanism and triangular time course. `winner_peer` is the close synchronous emulation; `peer_membrane` preserves same-bin feature spikes and applies only the peer membrane decrement.

## Active current top-five design requirements

- output semantic WTA remains enabled; do not apply hidden retinotopic inhibition in decoder/head
- triangular threshold adaptation and peer_membrane inhibition ramp from zero over 50% of training; hidden winner_peer gating stays off until the warm-up ends, while output class WTA stays on
- PLIF beta and threshold receive 2x base LR; mechanism parameters use base LR
- write new runs only to `artifacts/ablation/top_five_current top-five design/`
- preserve v1/v2 checkpoint loading and results
- diagnostics: class support/predictions, per-layer spike rates, beta/threshold, fInst/fLong/TThresh

## Finalization gates

Do not replace canonical `model.py` from one seed. Require complete current top-five design benchmark, rare-class diagnostics, seeds 17/101/2026, timestep sensitivity, and quantized dynamics validation.
