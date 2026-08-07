# Progress

## Working now

- DDD17 modality-first loader for `events/{train,test}` and `labels/{train,test}`
- six-channel Ev-SegNet direct encoding
- six-class spiking semantic head
- completed same-seed ten-model benchmark
- preserved round-one definitions in `top_ten_models.py`
- shared neuron and layer primitives in `model_components.py`
- five new PLIF/homeostasis/competition contenders in `top_five_models.py`
- canonical-only `model.py`, currently set to `v10_fpga_hybrid`
- separate top-ten and top-five benchmark CLI/Compose commands
- checkpoint field `model_suite` for correct evaluation dispatch
- unit tests for all 10 old models, all 5 new models, PLIF gradient, f_inst winner, and f_long/T_thresh timing
- local synthetic test result after refactor: 10 passed

## Measured round-one result

- winner: `v10_fpga_hybrid`
- seed: 17
- train / held-out samples: 2048 / 512
- epochs: 10
- mIoU: 0.3130
- pixel accuracy: 0.7871
- parameters: 44,016
- output spike rate: 0.1412

## Open issues

- object IoU was zero for the round-one winner and nearly all models
- human IoU was zero for all ten models
- class distribution, class presence after resize, prediction counts, and confusion matrix are not yet recorded
- top-five benchmark is not yet measured
- top-five winner is not yet confirmed across seeds
- PLIF has not been quantized to a hardware-compatible leak
- no measured FPGA synthesis, latency, power, or resource results

## Next action

Run Docker lint/tests, then execute `docker compose run --rm benchmark-top-five` using the same seed and budget as round one.
