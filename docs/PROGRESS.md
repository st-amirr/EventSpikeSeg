# Progress

## Working now

- DDD17 six-channel semantic loader and deterministic bounded subsets
- canonical `model.py` still fixed at `v10_fpga_hybrid`
- frozen completed ten-model structural benchmark in `top_ten_models.py`
- completed structural top-five registry in `top_five_models.py`
- active accuracy-oriented top-three registry in `top_three_models.py`
- PLIF with learnable beta and base thresholds
- local triangular threshold adaptation
- stem-only peer-membrane inhibition
- output class WTA and spike-count semantic readout
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

## Active accuracy top three

- `t01_spike_pyramid_concat` — 63,147 params; concatenated d1/d2/d4 spike context + binary channel selection + concatenative decoder.
- `t02_dualpath_detail` — 24,211 params; compact semantic encoder + persistent high-resolution spiking detail stream.
- `t03_deep_attention_fpn` — 108,781 params; four-stage encoder + low-resolution binary spike-mask attention + concatenative FPN.

## Validation completed locally

- focused top-three test module passes `2/2` in the local lightweight environment;
- `top_three_models.py`, updated `train.py`, and the top-three test module compile successfully;
- forward/backward passes complete for all three contenders with finite gradients;
- semantic logits have the standard `[N,6,H,W]` shape and auxiliary logits remain available;
- measured local parameter counts are 63,147 / 24,211 / 108,781;
- authoritative Ruff/full-suite validation still needs the Docker environment.

## Open issues

- rare-class IoU remains the dominant accuracy limitation;
- the new multiscale concatenation, detail preservation, and low-resolution spike attention hypotheses have not yet been measured on real DDD17;
- learned continuous neuron dynamics and learned attention thresholds remain unquantized;
- the eventual winner still needs the larger-budget/multi-seed/timestep and integer-reference gates before canonical promotion.

## Next action

Run `docker compose run --rm lint`, `docker compose run --rm test`, then `docker compose run --rm benchmark-top-three`. Compare mIoU first, then rare-class IoU/predicted-pixel counts, layer spike rates, parameter count, and hardware complexity before deciding whether to merge features into the final candidate.
