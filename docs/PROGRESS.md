# Progress

## Working now

- DDD17 six-channel semantic loader and deterministic bounded subsets
- canonical `model.py` now contains the post-ablation `final_dualpath_wide32` candidate (~132k params)
- frozen completed ten-model structural benchmark in `top_ten_models.py`
- completed structural top-five registry in `top_five_models.py`
- completed/frozen accuracy-oriented top-three registry in `top_three_models.py`
- PLIF with learnable beta and base thresholds
- local triangular threshold adaptation
- stem-only peer-membrane inhibition
- canonical independent spiking class populations with temporal spike-count semantic readout
- explicit 3- or 4-stage channel schedules
- configurable stem and first-block kernel size
- dynamic `enc4_spikes` activity/evaluation diagnostics for the deep contender

## Completed evidence

### Structural incumbent

`v10_fpga_hybrid`: mIoU 0.3130, pixel accuracy 0.7871, 44,016 parameters, output spike rate 0.1412 under the full round-one protocol.

### Latest neuron-mechanism screen

Protocol: seed 17, 5 epochs, 256 train, 128 held-out, 64×64, 8 internal timesteps.

| architecture | mIoU | pixel accuracy | spike rate |
| --- | ---: | ---: | ---: |
| `f05_v02_light_peer_membrane_inhibition` | 0.1991 | 0.7607 | 0.0616 |
| `f02_v10_plif_threshold_adaptation` | 0.1459 | 0.7395 | 0.0470 |
| `f01_v10_plif_threshold_wta` | 0.1402 | 0.7334 | 0.0457 |
| `f04_v03_dilated_threshold_adaptation` | 0.1366 | 0.7217 | 0.0513 |
| `f03_v10_plif_winner_peer_inhibition` | 0.1233 | 0.7384 | 0.0415 |

Selected mechanism base: PLIF + learnable threshold + stem peer-membrane inhibition + encoder triangular threshold adaptation.

## Completed structural top five

Protocol: seed 17, 8 epochs, 2,048 train, 512 held-out, 64×64, 15 timesteps, batch 14, LR 0.002.

| architecture | mIoU | parameters | useful evidence |
| --- | ---: | ---: | --- |
| `f05_compact16_dilated` | **0.2596** | **21,491** | best overall/efficiency |
| `f02_wide32_multiscale` | 0.2284 | 77,751 | best object IoU in round |
| `f04_deep4_dilated` | 0.2079 | 107,131 | strongest aggregate rare-class signal |
| `f01_base24_multiscale` | 0.1626 | 46,423 | weak controlled baseline |
| `f03_early5x5_multiscale` | 0.1482 | 49,111 | early 5×5 rejected |

None beat the 0.3130 incumbent. The round indicates that feature preservation/fusion is a higher-priority accuracy problem than simply adding width or parameters.

## Completed accuracy top three

- `t02_dualpath_detail` — **0.2728 mIoU**, 24,211 params; winner and evidence for a persistent high-resolution spiking detail stream.
- `t01_spike_pyramid_concat` — 0.1671 mIoU, 63,147 params; parallel multiscale concat did not recover accuracy.
- `t03_deep_attention_fpn` — 0.1555 mIoU, 108,781 params; extra depth/attention collapsed predictions toward dominant classes.

## Canonical candidate implemented

- 32/64/128 semantic path with extra residual depthwise/pointwise refinement;
- persistent 32-channel high-resolution detail path;
- serial dilation-2 context ×2;
- stronger 128→64→32 decoder with late semantic/shallow/detail concatenation;
- PLIF 1×1 cross-channel spike selector (no count-domain MLP);
- independent spiking class neurons and temporal argmax;
- SpikingJelly `Conv2d` wrappers and `ParametricLIFNode` charge equation when installed, with project-specific per-channel tau, fInst, fLong and exact operation order preserved;
- canonical-only 70/20/10 joint → backbone-frozen refinement → low-LR joint-unfreeze schedule.

## Validation completed locally

- focused top-three test module passes `2/2` in the local lightweight environment;
- `top_three_models.py`, updated `train.py`, and the top-three test module compile successfully;
- forward/backward passes complete for all three contenders with finite gradients;
- semantic logits have the standard `[N,6,H,W]` shape and auxiliary logits remain available;
- measured local parameter counts are 63,147 / 24,211 / 108,781;
- authoritative Ruff/full-suite validation still needs the Docker environment.

## Open issues

- rare-class IoU remains the dominant accuracy limitation;
- the completed top-three hypotheses are measured; the new scaled canonical candidate has not yet been trained/evaluated;
- learned continuous neuron dynamics and learned attention thresholds remain unquantized;
- `final_dualpath_wide32` is installed as the canonical candidate by design decision but still needs larger-budget/multi-seed/timestep and integer-reference gates before it is treated as the validated final/hardware-frozen model.

## Next action

Run `docker compose run --rm lint`, `docker compose run --rm test`, then `docker compose run --rm train-ddd17-smoke`. If these pass, train `final_dualpath_wide32` and compare it directly with the measured 0.3130 `v10_fpga_hybrid` baseline before larger multi-seed and quantization/hardware validation.
