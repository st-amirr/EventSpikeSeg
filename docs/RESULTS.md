# Results

Only measured results belong here.

## 2026-08-02 bootstrap validation

- Python unit suite: 39 passed in 2.11 seconds on Python 3.9.6 / PyTorch 2.2.2.
- Quantized/sparse reference subset: 9 passed in 1.36 seconds.
- Icarus Verilog 13.0 cocotb RTL unit suite: 5 passed in 1.92 seconds.
- Deterministic end-to-end smoke optimizer step: loss 1.54416668 and maximum Conv1
  weight change 0.00005585. This verifies gradient flow only; it is not an accuracy result.

No dataset accuracy, FPGA resources, timing, power, latency, or throughput has been measured.

## 2026-08-03 VHDL migration validation

- Python unit suite including YAML/language-policy regressions: 41 passed in 2.08 seconds.
- Quantized/sparse reference subset: 9 passed in 1.25 seconds.
- GHDL 6.0.0 cocotb VHDL-2008 unit suite: 5 passed in 6.34 seconds after the complete
  replacement of the earlier SystemVerilog sources.
- This is simulation/equivalence evidence only; synthesis and FPGA execution were not run.

## 2026-08-03 MEVDT loader and floating baseline

These measurements are historical results from the superseded box-objectness
architecture. Its generated checkpoints were deleted after the pixel-attention redesign
and the numbers must not be attributed to the new model.

- Official split index: 10,067 train frames / 51 sequences and 2,627 test frames / 12
  sequences, with zero sequence overlap.
- Parsed annotations: 7,816 train boxes and 2,010 test boxes.
- Balanced baseline training: 1,024 optimizer steps (512 positive, 512 background),
  91,371 events in 20×1 ms windows, mean sampled training loss `0.76926452`, final
  sampled loss `0.50544769`, and maximum Conv1 weight change `0.33447054`.
- Held-out balanced subset: 128 frames (64 positive, 64 background). Oracle-ROI binary
  classification accuracy `0.84375`; positive best-proposal mean IoU `0.062355`;
  proposal recall@0.5 `0.0`; background mean proposal count `0.71875`.
- These are early bounded-development measurements, not a converged full-dataset result.
  Oracle-ROI classification is not end-to-end tracking accuracy. The proposal result is
  currently inadequate and no FPGA performance claim is made.

## 2026-08-04 MEVDT pixel-attention repair and dynamics ablations

All values below use the same frozen balanced 128-frame official test subset (64 vehicle,
64 background), 50×1 ms input windows, and a two-spike (`0.04` rate) attention threshold.
They are bounded development measurements, not full-dataset or final-paper results.

- Plain LIF, seeded sequence-diverse 1,024 steps: predicted-attention classification
  `0.8125`, pixel IoU `0.507893`, Dice `0.673646`, precision `0.546974`, recall
  `0.876671`, and centroid error `11.6883` pixels.
- `f_inst`, seeded sequence-diverse 1,024 steps (selected localization checkpoint):
  classification `0.7890625`, pixel IoU `0.536611`, Dice `0.698434`, precision
  `0.594844`, recall `0.845712`, centroid error `11.1092` pixels, tracked centroid error
  `11.0857` pixels, and tracked center precision@20 pixels `1.0`.
- The selected `f_inst` checkpoint attends `0.672454%` of pixels on background frames.
  Only `3.125%` of background frames are completely empty, showing that isolated false
  pixels remain even though their spatial rate is low.
- `f_inst + f_long`, calibrated 1,024 steps: classification `0.921875`, pixel IoU
  `0.459352`, Dice `0.629529`, precision `0.517161`, recall `0.804280`, and centroid
  error `12.4594` pixels. This is retained as a classification-oriented ablation, not
  substituted for the higher-IoU localization checkpoint.
- On a 64-frame diagnostic subset, `f_inst` reduced Conv3 mean spike rate from
  `0.0106812` to `0.00180441` (about 83%) and reduced negative attention activity from
  `0.000590741` to `0.000374248`. These are software spike-rate measurements, not FPGA
  energy, power, latency, or resource results.

## 2026-08-04 post-repair validation

- Ruff passed over `src`, `tests`, scripts, and cocotb verification code.
- Python suite: 59 passed in 1.89 seconds.
- Quantization/sparse reference subset: 9 passed in 0.70 seconds.
- End-to-end surrogate-gradient smoke optimizer passed with loss `0.36416665` and
  maximum Conv1 weight change `0.00002223`.
- GHDL 6.0.0/cocotb VHDL-2008 unit suite: 5 passed in 5.07 seconds, with one cocotb
  experimental-runner API warning.
- These VHDL results cover the existing units only. The new attention pooling and
  centroid-moment RTL units do not exist yet and are the next hardware milestone.

## 2026-08-04 fully spiking readout retraining

The selected model replaces the analog classifier with bias-free synapses and class LIF
neurons. Training used 1,024 balanced optimizer steps (512 vehicle, 512 background),
50×1 ms windows, `f_inst` in the backbone, and independent class output neurons. It
processed 422,677 input events; mean sampled loss was `1.25049026`, final sampled loss
was `1.16529310`, and maximum Conv1 weight change was `0.19084743`.

On the same bounded 128-frame official-test development subset (64 vehicle, 64
background) at a two-spike (`0.04`) attention threshold:

- predicted-attention classification accuracy: `0.828125`;
- oracle-attention classification accuracy through the same spiking readout: `1.0`;
- pixel attention IoU `0.523869`, Dice `0.687551`, precision `0.609991`, recall `0.787708`;
- attention centroid detection rate `1.0` and mean error `7.1510` pixels;
- tracked centroid mean error `7.1101` pixels and precision@20 pixels `0.953125`;
- positive derived-proposal mean best IoU `0.453767` and recall@0.5 `0.4375`;
- background attention pixel rate `0.00679543`; background-empty rate `0.03125`.

These are bounded development measurements on a subset already used for architecture
selection, not untouched final-test or full-dataset results. No FPGA resource, timing,
power, latency, throughput, or end-to-end RTL result is claimed.

## 2026-08-04 fully spiking post-change validation

- Ruff passed over `src`, `tests`, scripts, and cocotb verification code.
- Python suite: 59 passed in 1.61 seconds.
- Quantization/sparse reference subset: 9 passed in 1.09 seconds.
- End-to-end surrogate-gradient smoke optimizer passed with loss `4.35416651` and
  maximum Conv1 weight change `0.00004750`.
- GHDL 6.0.0/cocotb VHDL-2008 unit suite: 5 passed in 5.57 seconds, with one cocotb
  experimental-runner API warning.
- RTL coverage is unchanged: these five units do not yet implement the attention gate,
  class synapse/LIF readout, centroid moments, or network-level integration.

## 2026-08-04 chronological evaluator compatibility diagnostic

The old 1,024-step fully spiking checkpoint predates the frozen validation metadata, so
it cannot participate in the new validation protocol. A bounded 16-frame chronological
official-test compatibility diagnostic executed only to exercise the evaluator. It
measured classification accuracy `0.9375`, classification F1 `0.952381`, pixel-attention
IoU `0.482934`, HOTA `0.04484`, MOTA `-1.1`, IDF1 `0.0`, tracking success AUC `0.08364`,
and center precision@20 `0.0`.

These numbers are neither a model-selection result nor a final test result. They expose
that deriving evaluation boxes from the untrained attention spread does not yet provide
acceptable identity-aware tracking, even while bounded classification and attention are
much stronger. The new three-seed sequence-validation cycle must replace this diagnostic.

## 2026-08-04 seed-17 complete-validation result

The recovered `mevdt_seed17_4096.pt` checkpoint was trained for 4,096 balanced optimizer
steps (2,048 vehicle and 2,048 background), with 1,706,400 input events. Mean sampled
loss was `1.10133147`, final sampled loss was `1.08295655`, and maximum Conv1 weight
change was `0.33393019`.

Chronological evaluation covered all 10 frozen validation sequences: 1,424 frames
(1,316 positive and 108 negative), at attention threshold `0.04`:

- attention IoU `0.70166466`, Dice `0.82468030`, precision `0.83290940`, recall
  `0.81661221`, centroid detection rate `0.84878419`, and detected-centroid error
  `5.58380965` pixels;
- predicted-attention classification accuracy `0.85674157`, oracle-attention accuracy
  `0.92977528`, and classification F1 `0.91632486`;
- tracking success AUC `0.42757390`, center precision@20 `0.69973661`, HOTA
  `0.34950928`, IDF1 `0.42708333`, MOTA `-0.08586626`, and tracked-centroid error
  `14.38388873` pixels;
- derived-proposal mean best IoU `0.57153286`, recall@0.5 `0.71200608`, background
  empty rate `0.07407407`, and background attention-pixel rate `0.006039`.

This is one of the required three validation seeds, not a final-test result. The seed-101
run stopped after step 2,816 of 4,096 (running mean loss `1.28222065`) and produced no
checkpoint, so it is not reported as a completed measurement.

## 2026-08-04 Windows recovery validation

- Clean Python 3.11 environment: 65 Python tests passed in 3.71 seconds; Ruff passed.
- Dataset partition: 8,643 training frames / 41 sequences and 1,424 validation frames /
  10 sequences.
- Docker RTL fallback: 5 GHDL 2.0.0/cocotb 1.9.2 VHDL-2008 simulations passed in
  2.76 seconds from a read-only `python:3.11-bookworm` container.
- Native Windows GHDL 6.0.0 compilation/elaboration succeeded, but cocotb's VPI DLL did
  not load. No native-Windows RTL pass is claimed.
- CPU-only Docker Compose image (`eventscnn-fpga:py311-bookworm`): 65 Python tests,
  Ruff, and 5 GHDL 2.0.0/cocotb 1.9.2 simulations passed with the project source mounted
  read-only. The final slim-based image measured 1.85 GB locally.

## 2026-08-04 seed-101 complete-validation result

The CPU-only Docker cycle trained `mevdt_seed101_4096.pt` for 4,096 balanced optimizer
steps (2,048 vehicle and 2,048 background) over 1,661,118 input events. Mean sampled
loss was `1.26139008`, final sampled loss was `1.10596359`, and maximum Conv1 weight
change was `0.53225434`.

Chronological evaluation covered all 10 frozen validation sequences and 1,424 frames:

- attention IoU `0.73515603`, Dice `0.84736591`, precision `0.84418588`, and recall
  `0.85056998`;
- predicted-attention classification accuracy `0.07584270`, oracle-attention accuracy
  `0.07654494`, and classification precision/recall/F1 all `0.0`;
- zero attention-centroid detections, zero tracked predictions, and therefore HOTA,
  IDF1, tracking success AUC, and center precision@20 all `0.0`;
- derived-proposal mean best IoU `0.56797291`, recall@0.5 `0.70136778`, background
  empty rate `0.07407407`, and background attention-pixel rate `0.00470250`.

This seed improves pixel attention over seed 17 but collapses the spiking classifier to
the background class, including when supplied oracle attention. It is retained as a
diagnostic checkpoint and cannot be selected as the working model.

## 2026-08-04 seed-101 saturation diagnosis and bounded repair

Matched trace evaluation used eight positive and eight negative validation frames per
checkpoint with both predicted and oracle attention. On positive predicted-attention
frames, seed 17 averaged `15.0` background and `20.25` vehicle spikes, while failed seed
101 averaged `48.125` and `46.125`. Failed-seed positive current means were approximately
`5.6396` and `0.5651`; peak candidate membranes were approximately `100.486` and `8.208`
against the `0.25` class-neuron threshold. The collapse is therefore output saturation,
not spike starvation or attention failure.

A 1,024-sample balanced seed-101 repair run divided bias-free class-synapse current by
32 using a five-bit power-of-two shift. It trained over 375,708 input events with mean
loss `1.19483720`, final sampled loss `1.60441113`, and maximum Conv1 weight change
`0.46832150`. Complete chronological validation covered all 10 frozen sequences and
1,424 frames:

- classification F1 `0.91809992`, precision `0.99555950`, recall `0.85182371`;
- HOTA `0.32863574`, IDF1 `0.37404886`, and MOTA `-0.18768997`;
- tracking success AUC `0.39830860` and center precision@20 `0.67778753`;
- attention IoU `0.71435160` and Dice `0.83337817`.

All three core metrics passed the strict nonzero gate. This is repair evidence, not the
final seed-101 result; the unchanged 4,096-sample repair run remains required.

## 2026-08-04 seed-101 full repaired result

The five-bit classification-current-scale repair trained for 4,096 balanced optimizer
steps (2,048 vehicle and 2,048 background) over 1,661,118 input events. Mean sampled
loss was `1.09092568`, final sampled loss was `1.56865382`, and maximum Conv1 weight
change was `0.83022296`.

Complete chronological validation covered all 10 frozen validation sequences and 1,424
frames:

- classification F1 `0.92926045`, precision `0.98634812`, recall `0.87841945`, and
  predicted-attention accuracy `0.87640449`;
- HOTA `0.46913726`, IDF1 `0.66144814`, and MOTA `0.48176292`;
- tracking success AUC `0.56710586`, center precision@20 `0.88937665`, and mean finite
  center error `7.20518806` pixels;
- attention IoU `0.75931163`, Dice `0.86319174`, precision `0.88441926`, and recall
  `0.84295932`;
- 1,239 predicted tracking detections against 1,316 ground-truth detections.

The strict classification-F1/HOTA/tracking-AUC gate exited successfully. This checkpoint
supersedes the bounded repair checkpoint while the original unscaled seed-101 checkpoint
is retained as regression evidence.

## 2026-08-04 seed-2026 full repaired result

The frozen five-bit class-current repair trained for 4,096 balanced optimizer steps over
1,617,987 input events. Mean sampled loss was `1.13391689`, final sampled loss was
`1.67189574`, and maximum Conv1 weight change was `0.64674801`.

Complete chronological validation covered all 10 frozen sequences and 1,424 frames at
the unchanged scale-4 attention-to-box decoder:

- classification F1 `0.93280000` and predicted-attention accuracy `0.88202247`;
- attention IoU `0.76867271` and Dice `0.86920854`;
- HOTA `0.47408017`, detection accuracy `0.46655858`, association accuracy
  `0.48997169`, IDF1 `0.67584579`, and MOTA `0.46808511`;
- tracking success AUC `0.55396782`, center precision@20 `0.87445127`, and mean finite
  center error `7.22719089` pixels;
- at IoU 0.5: 922 true positives, 394 false negatives, 304 false positives, and 2
  identity switches.

All nonzero core gates pass and the result closely reproduces repaired seed 101.

## 2026-08-04 attention-spread box-scale calibration

A training-only calibration sweep tested isotropic scales 2.5, 3.0, 3.5, and 4.0 plus
two asymmetric candidates. Scale 3 won both 256-frame and 512-frame calibration subsets;
on 512 frames it measured HOTA `0.306210` versus `0.230374` for scale 4.

Held-out cross-seed evaluation did not establish a universal HOTA improvement:

- repaired seed 2026: scale 4 HOTA `0.474080`, scale 3 HOTA `0.485307`;
- repaired seed 101: scale 4 HOTA `0.469137`, scale 3 HOTA `0.461110`.

Scale 3 improved several seed-101 secondary metrics but reduced its HOTA. Scale 4 remains
the global default pending the repaired seed-17 result; no validation-selected decoder
change is claimed.
