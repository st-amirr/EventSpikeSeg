# EventSpikeSeg-FPGA

Lightweight fully-spiking semantic segmentation for the Ev-SegNet semantic extension of DDD17, with a later sparse fixed-point FPGA target.

## Project layout

```text
src/eventscnn/model.py              canonical model only
src/eventscnn/model_components.py   shared convolution, LIF/PLIF, fInst/fLong primitives
src/eventscnn/top_ten_models.py     frozen round-one ten-model benchmark
src/eventscnn/top_five_models.py    preserved v1/v2 + active retinotopic-mechanism five
```

`model.py` remains `v10_fpga_hybrid` until a new contender beats the incumbent and passes multi-seed validation.

## DDD17 input

Host dataset:

```text
C:/Users/stamir/Desktop/Dataset/DDD17/
├── events/{train,test}/*.npy
└── labels/{train,test}/*.png
```

Docker mounts it at `/datasets/DDD17`.

Each sample is the Ev-SegNet six-channel event-statistic representation. The same six-channel sample is applied for `T` internal SNN updates; `T=20` is not 20 camera frames or 20 updates per second.

Classes: `flat`, `construction+sky`, `object`, `nature`, `human`, `vehicle`. Label `255` is ignored.

## Basic checks

```powershell
docker compose build
docker compose run --rm inspect-ddd17
docker compose run --rm lint
docker compose run --rm test
```

## Measured baselines

Round-one incumbent:

```text
v10_fpga_hybrid
mIoU            0.3130
pixel accuracy  0.7871
parameters      44,016
spike rate      0.1412
```

Top-five v1 was rejected; best mIoU was `0.2464`.

Top-five v2 was interrupted after three completed checkpoints:

```text
f01r_v10_plif_threshold       mIoU 0.2821
f02r_v10_plif_ratehomeo       mIoU 0.2047
f03r_v10_plif_grouped_inst    mIoU 0.1967
```

The v2 result indicates that PLIF + learnable threshold was useful, while the global rate controller and grouped top-k competition were harmful.

## Retinotopic-mechanism neuron mechanisms

The active redesign follows Debat et al. (2021), *Event-Based Trajectory Prediction Using Spiking Neural Networks*, more closely.

For neurons sharing one retinotopic location, the retinotopic mechanisms compute local membrane-energy `retinotopic_membrane_energy`. The retinotopic mechanisms use:

```text
UInst      = fInst * UPropInh
UMaxThresh = fLong * UPropInh
```

`triangular_threshold_adaptation` creates a local threshold process that rises for `adaptation_duration`, falls for another `adaptation_duration`, then returns to zero. Active processes at the same retinotopic location are summed. `peer_membrane_inhibition` reduces competing feature membranes at the same retinotopic location; `winner_peer_inhibition` additionally keeps only one same-bin winner.

Debat et al. optimized `fInst`, `fLong`, and `TThresh` with a genetic algorithm. In this supervised project, bounded continuous versions are learnable during surrogate-gradient training. Debat et al.'s physical-time `TThresh` values are not copied directly because the current DDD17 representation has artificial internal timesteps rather than Debat et al.'s physical event timing.

Two inhibition forms are available:

- `winner_peer`: closest synchronous approximation; strongest same-bin feature is used as the proxy for Debat et al.'s first asynchronous spike, peers are prevented from spiking and inhibited.
- `peer_membrane`: preserves same-bin feature spikes but applies the peer membrane inhibition.

Hidden retinotopic inhibition is restricted to early/encoder features. Semantic output class WTA is restored separately because it performed well in the round-one incumbent.

## Active top-five current top-five design

```text
f01_v10_plif_threshold_wta
  v10 + PLIF + learned threshold + output class WTA; no hidden retinotopic mechanism

f02_v10_plif_threshold_adaptation
  v10 + local triangular triangular threshold adaptation in encoder/context

f03_v10_plif_winner_peer_inhibition
  v10 + encoder winner_peer fInst + triangular threshold adaptation

f04_v03_dilated_threshold_adaptation
  efficient v03 dilated parent + triangular threshold adaptation

f05_v02_light_peer_membrane_inhibition
  lightweight recovered path + stem peer_membrane fInst + encoder triangular threshold adaptation
```

`triangular_threshold_adaptation` and `peer_membrane` inhibition ramp from zero over the first 50% of training. The discrete hidden `winner_peer` winner gate is kept off during that warm-up and enabled only afterward, while semantic class WTA remains active throughout. PLIF beta and threshold use 2x the base learning rate; learned `fInst`, `fLong`, and `TThresh` use the base learning rate without weight decay.

## Validate only the three completed v2 checkpoints

This retrains nothing and writes no model checkpoint. It evaluates the same deterministic 512-sample held-out subset and prints mIoU/per-class IoU for all three:

```powershell
docker compose run --rm validate-top-five-v2-completed
```

Do not run it simultaneously with a CPU-heavy training benchmark unless the slowdown is acceptable.

## Run retinotopic-mechanism benchmark

```powershell
docker compose run --rm benchmark-top-five
```

Outputs are isolated at:

```text
artifacts/ablation/top_five_current top-five design/summary.json
artifacts/ablation/top_five_current top-five design/checkpoints/
```

Historical results remain untouched:

```text
artifacts/ablation/top_five/
artifacts/ablation/top_five_v2/
artifacts/ablation/top_ten/
```

## Full single-model training

The canonical model is still selected through `.env`:

```powershell
docker compose run --rm train-ddd17
```

Do not run `promote-winner` until a current top-five design contender exceeds or materially improves on the `0.3130` incumbent and is confirmed with seeds 17, 101, and 2026, timestep sensitivity, and quantized-neuron validation.
