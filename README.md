# EventSpikeSeg

Fully spiking event-camera semantic segmentation for the Ev-SegNet semantic extension of DDD17, designed so the learned inference path can later be mapped to FPGA, neuromorphic hardware, or custom circuits.

## Repository layout

```text
src/eventspikeseg/model.py              canonical EventSpikeSeg model (`final_dualpath_wide32`)
src/eventspikeseg/model_components.py   shared PLIF/SNN/convolution primitives
src/eventspikeseg/top_ten_models.py     frozen round-one model registry
src/eventspikeseg/top_five_models.py    frozen structural top-five registry
src/eventspikeseg/top_three_models.py   frozen accuracy top-three registry
src/eventspikeseg/train.py              single training/benchmark engine for all suites
src/eventspikeseg/evaluate.py           checkpoint evaluation and visualizations
scripts/                                utility/diagnostic scripts only
docs/ARCHITECTURE.md                    current architecture and runtime contract
docs/DECISIONS.md                       chronological design decisions
docs/RESULTS.md                         measured experiment results
docs/PROGRESS.md                        current implementation/validation state
docs/BUGS.md                            open limitations and resolved failures
```

The historical model registries remain importable for reproducibility, but there is only one training engine. `train.py` handles `top-ten`, `top-five`, `top-three`, and `final`; the old standalone top-three benchmark runner is retired.

## DDD17 input

Expected host layout:

```text
DDD17/
├── events/{train,test}/*.npy
└── labels/{train,test}/*.png
```

Each Ev-SegNet semantic sample contains six event-statistic channels (histogram, timestamp mean, timestamp standard deviation for both polarities). Direct encoding reuses that sample over the configured number of internal SNN updates. These are neural timesteps, not raw chronological event bins.

Classes: `flat`, `construction+sky`, `object`, `nature`, `human`, `vehicle`. Label `255` is ignored.

If `--height` and `--width` are omitted, the stored dataset resolution is preserved. If they are provided, both must be supplied. `--train-samples` and `--validation-samples` accept `0` for all records, a fraction in `(0,1]`, or an absolute integer count greater than `1`.

## Main commands

```powershell
docker compose run --rm inspect-ddd17
docker compose run --rm lint
docker compose run --rm test
docker compose run --rm train-ddd17-smoke
docker compose run --rm train-ddd17
```

Historical ablations can still be reproduced through the same trainer:

```powershell
docker compose run --rm benchmark-top-ten
docker compose run --rm benchmark-top-five
docker compose run --rm benchmark-top-three
```

Historical suites use their frozen objective (`0.5 CE + 0.5 focal + 0.75 Dice`, plus historical auxiliary weights). The canonical final suite uses the current objective with CE coefficient `1.0` and its late refinement schedule.

## Measured architecture-search evidence

The measured historical incumbent remains:

```text
v10_fpga_hybrid
mIoU            0.3130
pixel accuracy  0.7871
parameters      44,016
spike rate      0.1412
```

The completed structural top-five selected `f05_compact16_dilated` at mIoU `0.2596` with only `21,491` parameters. The completed accuracy top-three selected `t02_dualpath_detail` at mIoU `0.2728` with `24,211` parameters. These experiments established the main design evidence carried into EventSpikeSeg: preserve high-resolution detail, retain moderate channel capacity, prefer depthwise/pointwise processing and simple dilation, and avoid a fourth downsampling scale or hard hidden winner gating.

Full rankings and per-class evidence are in `docs/RESULTS.md`; chronological interpretation is in `docs/DECISIONS.md`.

## Canonical EventSpikeSeg model

`final_dualpath_wide32` currently has **237,597 trainable parameters** and uses:

```text
6-channel input
→ 32/64/128 semantic encoder
→ projected PLIF residual bridges across downsampling
→ residual DW/PW refinement per scale
→ serial dilation-2 context ×2
→ residual parallel d1/d2/d4 context with PLIF 1×1 fusion
→ one bottlenecked low-resolution spike-mask attention residual
→ persistent high-resolution 32-channel detail path with asymmetric refinement
→ concatenative 64+64 mid-decoder fusion
→ late semantic32 + shallow32 + detail32 concatenation
→ 96→96 PLIF cross-channel selector
→ DW/PW final fusion/refinement
→ six independent spiking class populations
→ temporal spike-count argmax
```

Neuron dynamics remain PLIF with learnable per-channel beta/base thresholds, stem-only `peer_membrane` fInst, and encoder/context triangular fLong/TThresh. PyTorch provides tensors/autograd/optimization; SpikingJelly supplies compatible spiking convolution/PLIF/surrogate infrastructure while project-specific dynamics stay explicit.

There is no BatchNorm dependency, dense softmax attention, GAP/MLP inference gate, analog classifier, fourth downsampling stage, or hard hidden winner-peer WTA in the canonical path.

## Canonical training

The final model uses all available selected training data with a deterministic training-split validation holdout when `--validation-fraction` is set. The official DDD17 test split is reserved for final reporting rather than best-checkpoint selection.

The model exposes a late refinement schedule:

```text
0–70%   all layers train jointly
70–90%  semantic backbone frozen; detail/decoder/selector/heads refine
90–100% all layers unfrozen with an additional 0.25× LR multiplier
```

Final training validates after every epoch, saves the best validation-mIoU model, saves a recovery checkpoint every configured N epochs, and saves the last state separately. Auxiliary heads are training-only and are skipped in evaluation/inference.

## Accuracy status

`final_dualpath_wide32` is the canonical architecture by design, **not yet a measured accuracy claim**. It must be trained/evaluated under the larger final protocol and compared against the measured `0.3130` v10 baseline before hardware freezing. Rare-class IoU, especially `human` and `object`, remains the main accuracy risk.
