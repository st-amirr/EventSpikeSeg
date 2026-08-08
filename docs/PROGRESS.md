# Progress

## Working now

- DDD17 six-channel semantic loader and deterministic bounded subsets
- canonical `model.py` still fixed at `v10_fpga_hybrid`
- frozen completed ten-model structural benchmark in `top_ten_models.py`
- one active top-five registry in `top_five_models.py`
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

## Active structural top five

- `f01_base24_multiscale`
- `f02_wide32_multiscale`
- `f03_early5x5_multiscale`
- `f04_deep4_dilated`
- `f05_compact16_dilated`

## Validation completed locally

- targeted semantic/training suite passes after structural refactor
- canonical v10/top-ten strict state-dict compatibility remains covered by tests
- all active top-five models build and produce the expected semantic output shape
- the four-stage contender exposes `enc4_spikes`

## Open issues

- rare-class collapse remains severe in low-budget runs, especially nature/human/vehicle
- current mechanism screen is too small to compare against the 0.3130 full-budget incumbent directly
- learned continuous neuron dynamics remain unquantized
- structural contenders still need real DDD17 benchmarking and multi-seed confirmation

## Next action

Run `docker compose run --rm lint`, `docker compose run --rm test`, then `docker compose run --rm benchmark-top-five`. Compare mIoU, rare-class IoU, predicted-pixel counts, per-layer spike rates, and parameter count before selecting the structural winner.
