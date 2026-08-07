# Progress

## Working now

- DDD17 six-channel loader with bounded modality-first, split-first, and compact NPZ fixture support
- completed top-ten benchmark preserved
- failed first top-five definitions/checkpoints preserved and loadable
- five revised PLIF contenders implemented
- learnable per-channel beta and base threshold
- learnable rate-homeostasis tau, strength, and target firing rate
- grouped top-2 scoped competition
- independent spiking class-head accumulation
- complete-subset class weighting, focal/CE/Dice loss, activity floor, and dynamics warm-up
- checkpoint diagnostics for class support, predicted pixels, layer spike rates, and neuron parameters
- canonical `model.py` remains `v10_fpga_hybrid`

## Validation completed

- 17 local tests pass
- all five revised contenders build, backpropagate, and complete a synthetic benchmark
- legacy top-ten v10 state dict still loads strictly into the canonical model
- failed first top-five names remain buildable for checkpoint evaluation

## Measured incumbent

`v10_fpga_hybrid`: seed 17, mIoU 0.3130, pixel accuracy 0.7871, 44,016 parameters, output spike rate 0.1412.

## Measured failed top-five v1

Best: `f01_v10_plif_long`, mIoU 0.2464. `f04_v02_light_plif_inst_long` collapsed to zero spike rate. No v1 contender is eligible for promotion.

## Open issues

- revised top-five v2 has not yet been measured on real DDD17
- object and human class scarcity/collapse remains unresolved
- official test is still used as the held-out benchmark split
- learned continuous dynamics are not quantized or RTL-validated

## Next action

Run Docker lint/tests, then `docker compose run --rm benchmark-top-five`. Inspect mIoU, per-class IoU, class support/predictions, layer spike rates, and learned tau/threshold values before any promotion.
