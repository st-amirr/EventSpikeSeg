## 2026-08-31 — Simplify the active DSEC segmentation objective

Replace the final-run 0.5 pixel CE + 0.5 target-present macro CE + 0.3 Dice + 0.05 same-class region-consistency objective with a literature-aligned segmentation loss: 1.0 ordinary pixel CE + 0.3 Dice averaged over target-present classes + 0.10 auxiliary semantic CE + 0.02 boundary BCE. Keep the SNN activity regularizer because it constrains spike dynamics rather than semantic class weighting. Remove the macro-CE contribution and region-consistency contribution from the active final run. Historical benchmark suites retain their frozen loss profiles.

# Decisions

## 2026-08-29 — Size Docker shared memory for eight DSEC workers

Keep the user-selected eight CPU preprocessing workers with one prefetched record per
worker and raise the DSEC container `/dev/shm` ceiling from 256 MiB to 512 MiB. Eight
native 440x640 records occupy about 190 MiB before PyTorch multiprocessing queue,
in-flight transfer, and pinned-host-copy overhead, which caused the observed bus error
and `No space left on device` at 256 MiB. The ceiling is backed on demand and does not
reserve VRAM.

## 2026-08-29 — Train connected semantic regions without inference post-processing

Keep final Dice at 0.3 and add a 0.05 target-aware four-neighbor consistency term
over the final softmax probabilities. Penalize class-distribution discontinuity only
between adjacent valid pixels whose ground-truth classes match; do not smooth across
true class boundaries or ignore-index borders. Reduce the training-only boundary-head
BCE from 0.05 to 0.02 because validation predictions remain excessively aligned to
sparse event edges. Reuse the Dice softmax and compute Dice per class without a dense
one-hot target to contain training memory. The new loss adds no inference parameters,
post-processing, latency, or FPGA hardware.

## 2026-08-27 — Make six broad DSEC classes the active 140k training and ASIC target

Replace the active eleven-output semantic head with six outputs while retaining the exact
v8 spike-preserving backbone and native 440x640 input. Remap source labels as follows:
`road|sidewalk -> flat`, `sky|building|fence|wall -> construction+sky`,
`pole|traffic-sign -> object`, `vegetation -> nature`, `person -> human`, and
`vehicle -> vehicle`. The active readout is therefore 16->6, with 149,835 registered
parameters, 149,423 executed inference parameters, and 143,824 executed synaptic weights.
The 25 PLIF populations and their 30,976,000 logical membrane states do not change.

Give the six-class data contract its own protocol version and checkpoint directory so an
eleven-class checkpoint cannot be partially resumed. Preserve `--dsec-classes 11` only
for reproducibility; the active Docker training service and ASIC exporter require six.

## 2026-08-05 — Reset from MEVDT tracking to DDD17 segmentation

Tracking, box decoding, alpha-beta tracking, global classification, and MEVDT metrics are inactive. The task is six-class semantic segmentation using the Ev-SegNet DDD17 representation.

## 2026-08-05 — Preserve the six event-statistic channels

The six channels are polarity histogram, timestamp mean, and timestamp standard deviation pairs. They are repeated as direct current over internal SNN steps and are not reinterpreted as chronological bins.

## 2026-08-06 — Preserve the completed ten-model experiment separately

Round one completed with `v10_fpga_hybrid` highest at mIoU 0.3130. The complete preset registry is moved to `top_ten_models.py`; it remains reproducible but is no longer part of the canonical production module.

## 2026-08-06 — Keep model.py canonical-only

`model.py` contains one architecture interface. It currently installs the measured round-one incumbent. Experimental architectures belong in explicit experiment files and may not be added back to `model.py`.

## 2026-08-06 — Run a spike-native top-five round

The second round tests combinations derived from v10, v03, v02, and v08 using PLIF, feature-map threshold adaptation with an explicit duration, and selected hidden-layer inhibition. Ordinary BN and GAP gating are not included because this round targets mechanisms that remain meaningful during neuromorphic inference.

## 2026-08-06 — Do not enable hidden inhibition in every contender

Cross-channel winner-take-all may improve sparsity but can remove simultaneous semantic features. It is therefore isolated to two of five contenders rather than treated as automatically beneficial.

## 2026-08-06 — Treat PLIF as trainable, not yet hardware-exact

PLIF learns continuous per-channel retention. The eventual FPGA model must quantize it to an integer-friendly leak, then run accuracy and bit-exact regression tests before PLIF can be claimed as deployed.

## 2026-08-06 — Round-one zero-IoU classes are an open data/training issue

Object and human class performance cannot be solved by architecture ranking alone. Before final selection, record class pixel counts, image-presence counts, prediction counts, and confusion matrices at the benchmark resolution.

## 2026-08-07 — Reject the first PLIF/adaptation top five as final models

The first round-two winner reached only mIoU 0.2464 versus the incumbent 0.3130, and the lightweight `f04` emitted zero output spikes. Preserve the definitions/checkpoints for diagnosis but do not promote them.

## 2026-08-07 — Replace fixed adaptation hold with learnable continuous persistence

A discrete integer hold timer cannot receive useful gradients through standard backpropagation. Revised rate adaptation learns a bounded continuous `tau`, with retention `exp(-1/tau)`, plus per-channel adaptation strength and target firing rate. Quantize these only after architecture selection.

## 2026-08-07 — Make adaptation bidirectional and rate-based

Use spatial mean spike rate instead of feature-map `amax`. Threshold adaptation may become negative for silent channels and positive for overactive channels, bounded around the learnable base threshold.

## 2026-08-07 — Remove hard class-head WTA from revised contenders

Independent output class neurons accumulate spikes and compete only through final temporal argmax. This preserves a fully spiking learned output while allowing gradients to reach rare classes.

## 2026-08-07 — Restrict hidden inhibition rather than apply it globally

Only grouped top-2 competition is allowed, and only in the encoder or stem of selected contenders. Global one-winner competition caused severe information loss and dead-layer behavior.

## 2026-08-07 — Separate revised results from failed top-five results

This rerun was temporarily separated from the failed first attempt for diagnosis. That versioned active-directory convention is now retired: the completed structural five lives in `artifacts/ablation/top_five/` and the active three lives in `artifacts/ablation/top_three/`.

## 2026-08-07 — Use the completed mechanism screen to freeze neuron dynamics for structural search

The completed five-model screen used seed 17, 5 epochs, 256 training samples, 128 held-out samples, 64×64 output, and 8 internal timesteps. `f05_v02_light_peer_membrane_inhibition` ranked first at mIoU 0.1991. `f02` threshold adaptation alone ranked second at 0.1459, while hidden `winner_peer` inhibition ranked last at 0.1233 and drove `enc3` spike rate to approximately 0.00015.

Decision: the next top-five holds neuron dynamics constant as PLIF + learnable threshold + stem-only `peer_membrane` inhibition + encoder triangular threshold adaptation. Keep affine scaling, residual paths, auxiliary supervision, and semantic output class WTA. Do not use hidden `winner_peer` gating in the active five.

Reason: this separates the next question—network width, receptive field, depth, and context—from the already-screened inhibition question. The low-budget run is sufficient for mechanism selection but not for promotion accuracy claims.

## 2026-08-07 — Make width, early kernel size, and encoder depth explicit architecture variables

Add explicit channel schedules, configurable stem/first-block kernel sizes, and optional fourth encoder scale to the shared segmentation backbone. Preserve the original three-scale module layout for the canonical/top-ten models.

The active five are:

- `f01_base24_multiscale`: 24/48/96, 3×3, multiscale context
- `f02_wide32_multiscale`: 32/64/128, 3×3, multiscale context
- `f03_early5x5_multiscale`: 24/48/96, 5×5 stem and first depthwise block
- `f04_deep4_dilated`: 24/48/96/128, four encoder scales, single dilated context
- `f05_compact16_dilated`: 16/32/64, single dilated context

This replaced the previous top-five definitions. `TOP_FIVE_PRESETS` is now the single completed structural registry; the active search moved to `TOP_THREE_PRESETS`.

## 2026-08-08 — Complete the structural top-five and move the search toward feature preservation

The fixed-dynamics structural benchmark completed with seed 17, 8 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, 15 internal timesteps, batch 14, and learning rate 0.002.

Measured ranking:

- `f05_compact16_dilated`: mIoU 0.2596, 21,491 parameters
- `f02_wide32_multiscale`: mIoU 0.2284, 77,751 parameters
- `f04_deep4_dilated`: mIoU 0.2079, 107,131 parameters
- `f01_base24_multiscale`: mIoU 0.1626, 46,423 parameters
- `f03_early5x5_multiscale`: mIoU 0.1482, 49,111 parameters

Decision: do not promote any of these models. `v10_fpga_hybrid` remains the 0.3130 mIoU incumbent.

Findings used for the next round:

- compact `16/32/64` + a single dilated context gives the strongest overall accuracy/parameter tradeoff, so more parameters alone are not the answer;
- moderate width helped feature diversity and produced the best object IoU in the round (`0.0141`);
- the four-stage model produced the best aggregate rare-class signal, especially nature (`0.0712`) and vehicle (`0.1230`), so the deep encoder is extracting useful semantics that are being lost during decoding;
- early 5×5 processing is rejected;
- averaged multiscale branches are rejected for the next round because they erase branch identity and underperformed the simpler single-dilation path.

## 2026-08-08 — Create a separate top-three accuracy search

Create `top_three_models.py` instead of modifying the canonical model or the completed top-five registry. The three models isolate three accuracy hypotheses:

- `t01_spike_pyramid_concat`: preserve dilation-1/2/4 branch identity with channel concatenation, binary spike-count channel selection, and a spiking 1×1 fusion; use concatenative decoder skip fusion.
- `t02_dualpath_detail`: retain the compact semantic path but add a narrow persistent high-resolution spiking detail stream for small classes and boundaries.
- `t03_deep_attention_fpn`: retain four-stage semantic depth, add low-resolution spike-driven binary-mask attention, and use a concatenative FPN decoder to restore shallow spatial information.

The parameter targets are approximately 63k, 24k, and 109k respectively. Around 100k parameters is acceptable for an accuracy candidate, but fewer parameters win when validation accuracy is effectively equivalent.

## 2026-08-08 — Keep attention spike-oriented

Do not introduce conventional dense softmax self-attention into the active FPGA/neuromorphic search. The top-three may use:

- spike-count channel selection with a hard binary forward gate;
- low-resolution Q/K binary coincidence, channel accumulation, learned comparison threshold, and V masking;
- concatenation followed by spiking 1×1 mixing.

This is informed by SLTNet's evidence for multi-receptive-field event features, channel interaction, multi-level decoder restoration, and spike-driven masked attention, but the project tests smaller hardware-oriented modules rather than reproducing the full SLTNet network.


## 2026-08-09 — Complete the top-three search and select the dual-path mechanism

The accuracy-oriented top-three benchmark completed at seed 17 with 8 epochs, 2,048 training samples, 512 held-out samples, 64×64 output, and 15 internal timesteps. Results were `t02_dualpath_detail` mIoU 0.2728 / 24,211 parameters, `t01_spike_pyramid_concat` 0.1671 / 63,147, and `t03_deep_attention_fpn` 0.1555 / 108,781. T2 therefore provides the strongest new structural evidence: preserve a persistent high-resolution detail stream and fuse semantic + shallow + detail spikes late. T3's extra depth/attention is rejected for the canonical model because its predictions collapsed toward the two dominant classes.

## 2026-08-09 — Install the initial scaled spike-native dual-path candidate (later extended)

Replace the old `v10_fpga_hybrid` architecture in `model.py` with `final_dualpath_wide32`, while preserving `v10` in the frozen top-ten registry as the measured 0.3130 mIoU incumbent. The new candidate uses a 32/64/128 three-scale semantic encoder, extra residual depthwise/pointwise refinement per scale, a persistent 32-channel high-resolution detail path, two serial dilation-2 context blocks, a stronger decoder, and late semantic/shallow/detail concatenation. At this revision, do not add a fourth spatial scale, early 5×5 processing, averaged parallel multiscale context, dense softmax attention, or the failed T3 attention architecture wholesale. This restriction is later refined: one bottlenecked low-resolution residual spike-mask attention block is reintroduced as an additive feature, without the fourth T3 scale/FPN design. The candidate is not yet an accuracy claim; it requires larger-budget and multi-seed validation.

## 2026-08-09 — Try comparator-only spike-count selection and independent class spikes (selector later superseded)

For the canonical circuit-oriented path, replace the top-three count-domain MLP channel selector with one learned activity threshold per fused channel. Inference is spike counting, comparison, and binary AND gating only. Also disable hard per-timestep semantic class WTA in the canonical head: six independent spiking class populations accumulate evidence and final segmentation uses temporal spike-count argmax. This remains fully spiking while avoiding early suppression of rare class evidence. Historical benchmark definitions remain unchanged.

## 2026-08-09 — Use SpikingJelly as the PLIF/convolution infrastructure layer

Keep PyTorch as the tensor/autograd/optimizer substrate, but require SpikingJelly public `activation_based` components for learned synaptic stages. `SpikingStage` uses the SpikingJelly `Conv2d` synapse layer, and `ParametricLIF` delegates its charge equation to SpikingJelly `ParametricLIFNode`. Preserve the already-benchmarked per-channel beta by feeding a per-channel reciprocal-tau tensor into the SpikingJelly PLIF charge equation. Custom dynamic threshold, peer-membrane inhibition, triangular threshold adaptation, reset ordering, and hardware-visible state remain explicit project code. There is no conventional PyTorch Conv2d model fallback.

## 2026-08-09 — Add late decoder/detail refinement training

The canonical model trains all layers jointly through 70% of epochs. From 70% to 90%, freeze only the semantic backbone (stem, encoder, and semantic context) while keeping the high-resolution detail path, decoder/fusion, auxiliary head, and class head trainable; auxiliary CE/focal coefficients rise from 0.15 to 0.30 during this phase. At 90%, unfreeze all layers and apply an additional 0.25 learning-rate multiplier on top of the existing cosine decay for final joint tuning. Completed benchmark models have no refinement schedule and retain their original training behavior. The main segmentation CE coefficient is 1.0.


## 2026-08-09 — Replace comparator-only final selector with PLIF cross-channel selector

The comparator-only selector was more circuit-minimal but discarded T2's learned cross-channel relationships. The canonical `final_dualpath_wide32` therefore uses a spike-driven 96→96 1×1 synaptic projection followed by PLIF selector neurons. Selector spikes are reduced to binary per-channel enables and gate the fused semantic/shallow/detail spikes. This preserves cross-channel learned selection while keeping inference spike-native: active input spikes cause stored 1×1 weights to be accumulated into PLIF membranes, followed by threshold/fire gating. No dense count-domain MLP or softmax is used. Historical T2 remains unchanged for reproducibility. The canonical model is now approximately 141k trainable parameters.


## 2026-08-09 — Scale the canonical model by additive spike-native features

Decision: expand `final_dualpath_wide32` from the ~141k revision to 237,597 trainable parameters. Hardware simplicity alone is no longer a reason to remove an accuracy-oriented feature; features are excluded only when prior ablations give meaningful negative evidence or when they require a fundamentally dense/non-spiking inference path.

Added:
- projected cross-scale PLIF residual bridges (`32->64`, `64->128`) to reduce information loss through strided thresholded stages;
- residual parallel d1/d2/d4 depthwise context while retaining the existing serial d2 context;
- one low-resolution bottlenecked spike-mask attention residual;
- concatenative 64+64 mid-decoder fusion;
- asymmetric spike-native detail refinement;
- a second deep auxiliary head used only during training.

Retained unchanged:
- 32/64/128 three-scale semantic backbone;
- persistent 32-channel high-resolution detail path;
- PLIF, learnable threshold, stem-only peer-membrane inhibition, and encoder/context triangular threshold adaptation;
- late semantic+shallow+detail concatenation;
- 96->96 PLIF cross-channel selector;
- independent class spiking neurons with temporal count decision;
- 70/90% freeze/refinement schedule and CE coefficient 1.0.

The deep auxiliary loss is intentionally weaker than the mid auxiliary loss: 0.10 CE + 0.10 focal normally and 0.20 + 0.20 during decoder/detail refinement.


## 2026-08-09 — Consolidate all architecture suites into one trainer

Remove the standalone top-three training implementation. `train.py` is the single engine for `top-ten`, `top-five`, `top-three`, and `final`, while `top_*_models.py` contain definitions only. Preserve historical reproducibility by pinning top-ten/top-five/top-three to the recorded `0.5 CE + 0.5 focal + 0.75 Dice` objective and historical test-split evaluation. Keep the final suite on CE `1.0`, training-split validation holdout, per-epoch best-model selection, periodic checkpoints, and the 70/90% refinement schedule.

The active evaluation path must point to `final_dualpath_wide32_seed17.pt`; promotion of the completed T2 top-three winner is historical-only and uses a separately named checkpoint.

## 2026-08-09 — Apply lossless native-resolution memory cleanup

Keep the same FP32 math, T, BPTT, resolution, and model dynamics while removing avoidable RAM use: direct encoding uses a stride-0 temporal view rather than cloning T copies; old batch graph references are released immediately; gradients are cleared with `set_to_none=True` before the next forward; auxiliary heads are skipped in eval/inference; and native-resolution `output_size=None` checkpoints are handled by `evaluate.py`. Do not silently enable activation checkpointing, lower precision, truncated BPTT, or reduced resolution because those trade CPU or change the training calculation.


## 2026-08-09 — Remove obsolete project debris and archive the completed search plan

Keep `src/eventspikeseg/` limited to active runtime/training code plus frozen architecture registries. Delete the obsolete standalone `benchmark_top_three.py`, MEVDT/EventSCNN-only diagnostic scripts, generated `.ruff_cache`, and the PowerShell RTL wrapper that targeted a nonexistent Compose service. Retain the functional local-GHDL `scripts/run_rtl_tests.py`. Move `ddd17-semantic-ablation.md` from `docs/exec-plans/active/` to `completed/` after recording the measured top-three outcome and the feature lineage into the 237,597-parameter canonical model.


## 2026-08-09 — Restrict canonical threshold adaptation to semantic encoder/context

Decision: introduce a canonical-only `encoder_context` threshold-adaptation scope. Historical `encoder` scope semantics remain unchanged. The final model no longer applies triangular threshold adaptation to the full-resolution stem/x1, custom detail branch, or auxiliary head; adaptation begins at x2 after the first spatial downsampling and remains active through x2/x3/context. This matches the intended architecture and removes unnecessary per-pixel temporal state without reducing channels, T, precision, or gradient horizon. Final parameter count becomes 237,597. Stateless convolution plus affine current transforms are vectorized across the T×N batch dimension while PLIF/LIF updates remain sequential, preserving identical temporal dynamics and gradients. The training output contract also uses scalar activity rates instead of retaining complete hidden spike sequences.


## 2026-08-14 — Supersede repeated-static direct encoding with temporal-v2

The 2026-08-05 decision to repeat each six-channel Ev-SegNet sample over internal SNN timesteps is superseded. The timestep sweep and later checkpoint plateau showed that this protocol gives the recurrent neurons repeated current without new sensory evidence and leaves rare classes collapsed.

Decision: remove repeated-static support rather than maintain backward compatibility. Every new sample must contain chronological evidence.

Two supported representations are now first-class:

- `sequential-6ch`: `T` strictly consecutive Ev-SegNet statistical samples from one sequence/interval; target is the final mask.
- `raw-events`: original DDD17 events in a fixed physical interval ending at the label timestamp, divided into `T` ON/OFF count bins.

Training/validation splits are made by complete `sequence_id`, not random frames. The generated dataset-root `ddd17_temporal_manifest.json` is the authoritative source of semantic sequence boundaries and frame order; the runtime no longer generates or infers that chronology from filenames. Raw mode deliberately does **not** store or consume `timestamp_us`/`raw_event` alignment in the manifest: it resolves the canonical `raw/rec<ID>.hdf5` recording and actual APS timestamp in memory from `sequence_id` + `frame_index`. Checkpoints freeze the temporal protocol through a manifest digest plus SHA-256 fingerprint. Checkpoints from the removed repeated-static protocol are deliberately not resumable/evaluable through the current runtime.

Rationale: data chronology is now treated as part of the model contract. Architecture search should resume only after the chronological six-channel and raw-event baselines are measured.

### 2026-08-14 — Raw alignment is runtime data loading, not manifest preprocessing

Decision: remove the separate raw-manifest preparation command and all hard-coded full-dataset count checks. `DDD17RawEventDataset` resolves original DDD17 source frames and real APS timestamps during construction, caches each recording's timestamp table, and never mutates `ddd17_temporal_manifest.json`. The exact terminal-boundary export sample is supported only when its corresponding raw APS frame exists; larger indices fail. Timestamp units are explicit by dtype (float seconds, integer microseconds), and only well-defined raw HDF5 layouts are accepted. This keeps raw alignment in `data.py`, where input extraction belongs, and prevents paper totals from overriding the actual local dataset.

### 2026-08-14 — Supersede HDF5 raw alignment with installed NumPy event bins

The active dataset has no raw HDF5/event-list source. Its event files are dense `200×346×6` Ev-SegNet interval statistics. Exact within-interval `(t,x,y,p)` binning cannot be reconstructed from histogram/mean/std moments.

Decision: make `event-bins` the default input. Each SNN timestep is one strictly consecutive manifest interval; input channels are the two polarity histograms mapped from the stored `[-1,1]` encoding to nonnegative `[0,1]`. Timestamp mean/std channels are not treated as time. `sequential-6ch` remains an ablation. Active training/evaluation has no HDF5 dependency, and the compatibility `train-ddd17-raw` command routes to `event-bins`.

The indexed PNG target remains one class ID per pixel (0–5), while the network emits six spiking class maps. Dataset inspection must report event/label count mismatches; the current installation has 2,887 train event tensors and 10,001 train masks.

## 2026-08-15 — Replace multi-file bins with timestamp-scheduled continuous state

The 2026-08-14 multi-file `event-bins`/`sequential-6ch` decision is superseded.
Each installed NumPy tensor already covers one 50 ms interval and remains one loader
item. Stored order is `hist0,hist1,mean0,std0,mean1,std1`; the loader decodes this
to activity, mean, and standard deviation per polarity.

The input adapter schedules activity at mean and mean±std with weights 0.50/0.25/0.25
over ten 5 ms hardware-clock updates. This conserves activity but is explicitly a
moment approximation because the archive does not contain individual event tuples.
PLIF state persists across consecutive records and resets at sequence/frame gaps.
Training truncates BPTT after each record by detaching, not clearing, recurrent state.
Shuffle, multi-file windows, HDF5/raw readers, user-configured T/stride, and their
compatibility commands are removed. New checkpoints use `ddd17-timestamp-v3`.

The internal clock count is exposed as `--internal-updates` with default 10. It
must divide the physical 50,000 µs interval exactly and is fingerprinted. Continuous
state cleanup includes both project buffers and SpikingJelly's internal PLIF `v`/`w`
references so completed autograd graphs cannot overlap the next record.

## 2026-08-17 — Add DSEC-Semantic as an exact raw-event input contract

DSEC-Semantic is a separate dataset contract, not a conversion into DDD17 moment
maps. The installed eight training sequences contain 8,082 masks and the three test
sequences contain 2,809 masks. Their semantic timestamp files are approximately
50,000 µs apart (20 Hz), despite the historical ESS loader also supporting a 100 ms
subsampled setup.

For every usable label, read `[timestamp-50,000us, timestamp)` directly from the
sequence HDF5 stream using `ms_to_idx`; apply `t_offset`, rectify raw coordinates
with the supplied map, crop to the 640×440 semantic view, and schedule binary ON/OFF
input spikes into `internal_updates` equal physical clocks. Collisions within one
pixel/polarity/clock are binary rather than analog counts. Preserve PLIF state only
across consecutive labels of the same sequence and detach recurrent autograd history
after each mask-aligned record.

The canonical `EventSpikeSeg140k` learned feature topology is unchanged. Its input adapter may
bypass DDD17 moment reconstruction for an already scheduled two-polarity stream, and
its semantic head expands from six to the dataset-required eleven spiking class
populations. DSEC checkpoints use `dsec-raw-events-v1` so they cannot be mixed with
DDD17 checkpoints.

## 2026-08-17 — Add explicit sequential truncated BPTT for DSEC

Dense PyTorch training at ten raw-event clocks retains substantially more temporal
activation memory than model-weight memory. Add `--sequential-chunks`, defaulting to
one so existing training is unchanged. For values above one, divide `[T,N,2,H,W]`
into equal chronological chunks, compute and backpropagate an equally weighted loss
for each chunk immediately, preserve PLIF membrane/adaptation values, and detach
their gradient history before continuing. Optimizer and gradient-accumulation steps
remain record-based rather than chunk-based. This preserves all input clocks and the
forward state trajectory but deliberately truncates gradients at chunk boundaries.

## 2026-08-18 — Preserve surrogate gradients through hard spike gates

A DSEC run remained at zero output spikes and mIoU 0.0081 for six epochs even
though encoder and decoder spike rates were healthy. The loader was not dead: real
records delivered roughly 140k scheduled input spikes and validation showed nonzero
hidden activity. The failure was the neuron output expression `raw * hard_gate`.
When a neuron was below threshold, the hard Boolean gate also multiplied its
surrogate derivative by zero, so a silent class head could never learn toward its
threshold and weight decay pushed it further into silence. Keep the identical binary,
competition-gated forward spike, but use a straight-through expression whose backward
derivative is the surrogate derivative of `raw`. A regression test requires a
subthreshold PLIF neuron to emit zero forward while retaining nonzero input gradient.

## 2026-08-18 — Scale the fixed DSEC validation split with training coverage

The earlier generic greedy sequence split could overshoot a 10% request severely:
it selected `zurich_city_02_a` and the large `zurich_city_05_a`, producing 1,986
validation records (24.6%) and excluding that large route from training. Validation
coverage should instead scale with the amount of data active in each training epoch.

For `train_samples <= 0.5`, exhaustively choose one complete validation sequence;
for a larger fractional training coverage, choose two. Minimize distance from
`total_records × validation_fraction × active_train_fraction`; split seed 17 fixes
ties, and membership remains fixed for the run. On the installed 8,074 usable
records, `train_samples=0.5` selects only the 234-record `zurich_city_02_a`, leaving
7,840 records in the pool and 3,920 in each half-sampled epoch. At `0.7`, validation
uses `zurich_city_01_a` plus `zurich_city_02_a` (914 records).

Fractional training sampling remains independent within every non-validation
sequence, using one deterministic contiguous window per sequence per epoch. Exact
record membership is checkpoint-fingerprinted, so checkpoints from earlier DSEC
splits are not resumed.

## 2026-08-19 — Stabilize DSEC semantic-head optimization

Epoch-12 checkpoint inspection showed a real class collapse: 82.7% of validation
pixels were assigned to building, despite finite model/optimizer tensors and active
hidden spike rates. Three compounding optimizer choices were corrected. Reduce the
DSEC base LR from `1e-3` to `5e-4`; remove the historical `2x` multiplier on PLIF
beta/threshold parameters; and average soft Dice only over classes present in the
current target. Continue reporting the full per-class Dice vector. Median-frequency
class weights remain unchanged for this intervention so their effect can be isolated.

## 2026-08-19 — Keep EventSpikeSeg140k canonical and target digital neuromorphic FPGA inference

Canonical model naming is `EventSpikeSeg140k` for the ~140k deployment baseline and
`EventSpikeSegXL` for the optional 236,445-parameter expanded comparison. This naming
policy does not alter the trained canonical forward topology or parameters.

The canonical six-class model has 140,089 registered parameters, but its executed
inference graph uses 134,637. The inherited `refine2` block (5,056 parameters) is
registered but never called; the 396-parameter auxiliary head is training-only. FPGA
deployment targets the executed inference graph only.

The primary hardware direction is **custom VHDL-2008 on ZCU104**. PyTorch/SpikingJelly
remains the training and floating-point golden-reference stack. Convolution kernels are
shared synaptic weights/connectivity; PLIF feature-map elements are logical neuron states.
FPGA inference represents weights, membrane/current, beta, thresholds, and adaptation
with deterministic fixed-point numbers rather than physical voltages/currents.

The hardware should stay as neuromorphic as practical despite being fully digital:
inter-layer communication is binary spikes/events, active spike addresses trigger shared
weight additions, PLIF state persists in banked memory, and inactivity-aware scheduling
should suppress unnecessary work. The baseline preserves learned per-channel beta with a
quantized coefficient; shift-only/power-of-two leakage is an optimization only if
bit-level behavior and semantic accuracy are revalidated.

Scale is handled with reusable coarse-grained synaptic-accumulator + PLIF processing
elements, not one datapath per logical neuron. The same PEs are time-multiplexed across
spatial tiles/channels/stages while membrane/adaptation state remains in BRAM/URAM/
LUTRAM. Start with exact full/tiled execution, then consider touched-address lists,
active-neuron lists, lazy decay, and clock-enable optimizations.

Nontrivial RTL items are the stem peer-membrane inhibition rule, triangular threshold
adaptation, and the selector's global binary channel enable. The selector `amax(H,W)` can
be implemented efficiently as a per-channel any-spike flag because selector outputs are
binary. Do not silently remove any of these mechanisms; approximations require
revalidation/fine-tuning.

Verification proceeds from SpikingJelly float to a bit-exact integer reference, VHDL RTL
simulation, Vivado synthesis/place-and-route, post-implementation timing simulation, and
representative-event SAIF/VCD power analysis. These Vivado results are estimates. Only
instrumented ZCU104 results may be called measured hardware power/latency.

## 2026-08-20 — Separate shared parameters from per-neuron runtime state for FPGA mapping

Do not use the ~140k parameter count as a proxy for logical PLIF state. Convolution weights
are spatially shared and beta/base threshold are shared per output channel, but every
executed PLIF output element `(layer,c,y,x)` retains its own membrane value. Summing the
37 inference PLIF populations gives `N_mem = (672+Nclass)HW + 480H2W2 + 1280H4W4`.
Corrected for `project2` executing before upsample, six-class DDD17 at 212x282 has
**51,089,456 independent membrane states**.

The threshold-adaptation-enabled scopes contain `352H2W2 + 1216H4W4` logical neurons, or **9,836,800**
at 212x282; each carries adaptation age and adaptation amplitude. These persistent states
are distinct from temporary synaptic-current accumulation and from sparse spike-event FIFOs.

FPGA execution should therefore keep weights/kernel connectivity static/shared while
virtualizing logical neuron state in addressable memory. A small physical PLIF PE array may
be reused across layers and spatial positions, but different logical neuron addresses must
never share one stored membrane value. For exact equivalence, all synaptic contributions for
a layer/timestep are accumulated first, then each PLIF is updated/thresholded once. Hidden
spikes may be processed input-centrically as `(c,y,x)` addresses, so dense sliding-window
convolution is not required. Lazy decay/touched-neuron-only updates remain later
optimizations because they change when decay is evaluated and must be proven equivalent
with reset, peer-membrane inhibition, and triangular threshold adaptation.

## 2026-08-21 — Preserve DSEC event density and supervise complete records

The original DSEC scheduler collapsed every repeated `(clock, polarity, y, x)` event to
one, discarding local event density. It also applied the complete semantic mask to each
temporal chunk independently, so the five-chunk profile imposed the same final target on
five partial 10 ms histories. Replace the external event value with
`min(log2(count + 1), 4)`, retaining unit value for a single event while compressing and
bounding bursts. Hidden inter-layer communication remains binary.

Retain all ten chronological 5 ms clocks but combine their time-normalized logits before
computing weighted CE, present-class Dice, and auxiliary CE. Each 50 ms record now yields
one semantic objective. Numeric membrane/adaptation state continues across consecutive
records and is reset only at epoch, validation, sequence, or frame-gap boundaries.
Chunking remains available for state-carry execution, but its outputs contribute to the
same full-window objective; the compose profiles use one chunk because exact nonlinear
full-window loss must retain the output graphs until backward.

This changes the DSEC temporal protocol to `dsec-log-count-events-full-window-v2`, so old
binary/partial-loss checkpoints are intentionally incompatible. EventSpikeSeg140k remains
the canonical deployment model; EventSpikeSegXL is an explicitly named comparison run.

## 2026-08-21 — Make DSEC deployment asynchronous and training timestamp-aware (superseded 2026-08-22)

The bounded-log/full-window decision above still described a clocked input model and is
superseded for DSEC. The final FPGA must accept sequential camera events directly; it must
not store 5 ms input bins or run a global neural timestep. Each touched neuron stores a
last-update timestamp, applies `beta ** (delta_us / 5000)`, receives the shared synaptic
weight, thresholds/resets, and immediately enqueues generated binary spikes. State carries
across semantic labels and resets only at sequence/frame gaps.

PyTorch/SpikingJelly remains the fast training backend. It accumulates chronological
source events into `internal_updates` fixed physical-time divisions, preserves linear
event multiplicity without log/cap, and supplies the fixed elapsed duration to the same
physical-time neuron equation. Event density never changes the number of training updates.
These divisions are a training approximation, not an FPGA input representation.

All packets in the 50 ms label interval contribute to one final semantic objective. For
memory-bounded XL training, first form the complete-record prediction without retaining
activation graphs, then restore initial neuron state and replay chronological chunks using
the one objective's output gradients. Keep the replay snapshot in host RAM to avoid a
second full persistent-state copy on the GPU. This is truncated state-gradient history,
but it is not multiple partial-history target losses. Logits/rates are normalized by
elapsed physical time so packet count does not change their scale.

The global spatial selector gate is incompatible with immediate event propagation. Replace
its `amax(H,W)` channel enable with a local retinotopic 1x1-PLIF binary gate. The new DSEC
protocol is `dsec-fixed-time-counts-async-fpga-v4`; older checkpoints are rejected.

## 2026-08-21 — Use EventSpikeSegXL as the detailed DSEC/FPGA implementation target

Promote `EventSpikeSegXL` from an undocumented capacity comparison to the active detailed
implementation target for the 11-class DSEC configuration at `241x351`. Retain
`EventSpikeSeg140k` as the compact reference/baseline; this decision does not rename either
Python model or claim that XL has already achieved better measured accuracy.

The instantiated XL/DSEC module has 237,115 registered parameters. Its custom forward omits
the inherited 5,056-parameter `refine2`; training additionally executes 726 parameters in
the mid auxiliary head and 4,566 in the deep auxiliary head. The deployed inference graph
therefore contains 226,767 parameters and 50 PLIF populations. FPGA export must omit the
dead block and both training-only heads.

For `H=241`, `W=351`, `H2=121`, `W2=176`, `H4=61`, and `W4=88`, XL inference owns
`683HW + 768H2W2 + 2144H4W4 = 85,639,973` membrane states. Its 26 threshold-adaptation-enabled
populations contain `416H2W2 + 2080H4W4 = 20,024,576` neurons, each with adaptation age
and amplitude. Direct asynchronous DSEC execution also requires one last-update timestamp
per membrane state. An illustrative exact store using 16-bit membrane, 16-bit age and
amplitude, and 32-bit timestamps is about 566.42 MiB before FIFOs, caches, accumulators,
and output counters. Therefore the XL baseline uses an external-DDR state store with an
on-chip banked tile/cache; an all-on-chip state claim requires a later quantified
compression/quantization result.

The parallel context and local Q/K/V spike-mask attention are part of the executed graph.
They require timestamp-tagged local join/rendezvous buffers so residual branches and Q/K/V
paths are combined deterministically without introducing a global spatial-frame barrier.

## 2026-08-22 — Freeze 140k and use permanent layer actors on U55C

This decision supersedes the 2026-08-21 XL target/platform mapping. The only FPGA target
is the two-input, 11-class `EventSpikeSeg140k`: 140,589 registered parameters, 134,807
executed inference parameters, 127,456 executed convolution weights, and 37 executed
PLIF populations. FPGA export hard-rejects XL and excludes inherited dead `refine2`, the
training-only auxiliary head, and surrogate gradients.

Instantiate all 37 executed populations as permanent layer actors. Each actor owns its
convolution address generator, synaptic accumulator lanes, PLIF/inhibition/adaptation
logic, output FIFO, and initialized local weight ROM. Do not share compute across layers,
reconfigure actors, or use partial reconfiguration. An actor may sequence its own lanes
over that actor's logical destinations. Clock/reset, timestamp input dispatch, HBM state
fabric, and final class readout remain permitted shared infrastructure.

Choose AMD Alveo U55C as the primary board and U280 as fallback. All executed int8
weights fit comfortably in local BRAM/LUTROM, but the corrected 140k graph has 72,843,333 logical
membranes and 14,023,680 adaptation-enabled neurons at 241x351. The baseline 16-bit
membrane, 32-bit timestamp, and two 16-bit adaptation fields require about 470.31 MiB
before queues/counters. Therefore exact persistent state uses in-package HBM2 behind
actor-local BRAM/URAM caches. This is not off-board DDR and does not change event-driven
execution.

Iteration 0 freezes the format/graph/export boundary before new integrated RTL: emit a
37-actor manifest, affine-folded int8 weight ROMs, quantized neuron/mechanism parameters,
and deterministic fixed-point rules; validate integer PLIF and sparse-state primitives;
then generate actor packages and layer-by-layer golden traces. Existing VHDL files remain
isolated historical primitives until they are proven against this new contract.

## 2026-08-22 — Replace the accelerator card with no-DDR Artix-7

This supersedes the U55C/HBM platform portion of the preceding decision, while retaining
the frozen 140k graph and 37 permanent actors. Use the conventional Digilent Nexys Video
with XC7A200T-1SBG484C. Do not use its 512 MiB DDR3 or any other external memory.

The device provides 13,140 Kibit = 1.604 MiB BRAM and at most 2,888 Kibit = 0.3525 MiB
distributed RAM. The dense 140k runtime state is 481.899 MiB, so BRAM alone is short by
468.705 MiB/293.209x. Even sacrificing all distributed RAM gives only 1.9565 MiB and
would leave insufficient LUT logic. Static int8 convolution weights are only 0.122 MiB
and do fit; persistent spatial neuron state is the incompatibility.

The only semantics-preserving route that might remain on this device is a lossless
zero-default sparse live-state table with no overflow eviction or spill. Full DSEC traces
must prove a worst-case occupancy bound including tags, values, queues, weights, and logic
margin. Until it passes, an all-on-chip full-resolution implementation is explicitly
classified as infeasible rather than assumed to fit.

## 2026-08-22 — Preserve named neuron runtime state in training checkpoints (superseded 2026-08-23)

Keep recurrent tensors nonpersistent in the ordinary PyTorch `state_dict`, because their
data-dependent shapes make strict weight loading fragile. Instead, only the best-model
checkpoint stores a separate `training_runtime_state` mapping keyed by executed layer name;
periodic and `last.pt` recovery checkpoints remain normal-sized. The canonical checkpoint
inherits the snapshot when the best checkpoint is copied to it. The snapshot contains the
membrane, adaptation, threshold-timer/adaptation, and physical-time state captured at the
end of the training epoch before validation resets or overwrites it. The format and scope
fields identify this as `layer-named-hardware-lif-v1` forensic state. Normal resume remains
epoch-boundary weight/optimizer restoration; replaying saved runtime state must be explicit
so it cannot leak one sequence into another.

This one-off forensic snapshot was removed on 2026-08-23. Best, periodic, last, and
canonical checkpoints now contain ordinary trainable model/optimizer/protocol state only;
they do not serialize data-dependent membrane, adaptation, or elapsed-time tensors.

## 2026-08-28 — Stabilize class learning with blended pixel and macro CE

Replace the final suite's pure per-record macro CE with 0.5 pixel-mean CE plus
0.5 target-present-class macro CE. Retain rare-class pressure without allowing a
very small person or traffic-sign region to determine the full record's CE gradient.
Increase present-class Dice from 0.2 to 0.3, use pixel-mean CE for the training-only
semantic auxiliary heads at weight 0.1, and reduce weighted edge-head BCE from 0.1
to 0.05. Keep focal and static class weights disabled, retain activity regularisation,
and continue evaluating exactly one objective after each complete 50 ms record.


## 2026-08-28 — Add state-safe raw-event augmentation

Enable training-only DSEC horizontal flip at probability 0.5, integer translation
within plus or minus six output pixels, and zero-to-five-percent event dropout. Apply
one spatial transform to the raw rectified event coordinates and aligned target mask;
all ten 5 ms updates in the 50 ms record share it. Because membrane state persists
across records, keep the spatial transform fixed for each recording sequence for the
complete run. Event dropout may vary deterministically by epoch and record without
moving surviving events. Fill translated mask borders with ignore index 255, preserve
event timestamps, polarities, multiplicities, and order, and leave validation untouched.

Move DSEC HDF5 reading, rectification, augmentation, mask loading, and temporal binning
off the main training process into two CPU DataLoader workers. Prefetch only one complete
record per worker into pinned host RAM and use non-blocking CUDA transfer. This overlaps
CPU preparation with GPU training without increasing the model's active-record VRAM
requirement or changing chronological delivery. Set the DSEC Docker shared-memory ceiling
to 256 MiB because the 64 MiB default cannot hold two native-resolution records plus
PyTorch multiprocessing queue overhead; this ceiling is consumed on demand and is not
reserved VRAM or an immediate host-RAM allocation.


## 2026-08-23 — Replace static class weights with macro per-class loss in every suite

DSEC person pixels occupy about 0.078% of the installed training masks and traffic-sign
pixels about 0.325%. A capped static weight cannot make their contribution comparable to
large road/building regions. For every suite, compute mean negative log-probability
separately for each target-present class and average those class means equally. Apply the
same macro rule to focal loss where a historical profile enables focal, and to semantic
auxiliary heads. Classes absent from a record have no positive
term, but their logits remain competitors in the softmax denominator. Retain 0.2 present-
class Dice, 0.1 auxiliary CE, 0.1 boundary supervision, and activity regularisation; keep
focal disabled in the final profile. Existing historical measurements remain records of
their original objectives; new comparison runs use the unified macro balancing rule.


## 2026-08-22 — Use 50 ms record-level, T=10 fixed-step FPGA inference

This supersedes the 2026-08-21 decision that made DSEC deployment direct asynchronous AER execution. Preserve the trained timing contract instead of translating the checkpoint to a new event-time neuron model.

DSEC still starts from exact raw `(t,x,y,p)` events, but both software training and baseline FPGA inference assign every event to one of ten chronological 5 ms slices inside the 50 ms semantic interval. Event multiplicity is preserved. The network therefore executes ten fixed PLIF updates per record and emits one segmentation result after temporal class-spike counting over the complete 50 ms interval.

The FPGA scheduling order is intentionally **layer-major over the complete T=10 record**. For layer `L`, process slices `t0..t9` sequentially using that layer's own persistent membrane/adaptation state, buffer its ten output spike slices, then let layer `L+1` consume that sequence. This is equivalent to the trained multi-step feed-forward graph because recurrent state is local to each PLIF population.

This scheduling choice is also the baseline state-memory strategy. Load a layer/state tile once, keep it resident while executing all ten 5 ms updates, and write its final state back after `t9`. Sparse event-address convolution remains enabled within each slice, so zero spike locations do not trigger synaptic additions. The baseline explicitly advances every required state in known 5 ms steps and therefore does not require a 32-bit `last_update_us` field per membrane. Timestamp/lazy-decay storage becomes an optional later optimization only if the integer reference proves exact equivalence.

The runtime is **not fully asynchronous**. The real-time throughput target is one complete 50 ms record every 50 ms (20 Hz); record acquisition and compute may be double-buffered. The ten internal 5 ms steps may not be collapsed into a single 50 ms PLIF update.

## 2026-08-23 — Native-resolution learned downsampling and continuous class readout

The 241x351 v6 graph plateaued below the required accuracy and discarded spatial evidence
before the first learned operation. Supersede it with the v7 `EventSpikeSeg140k` graph.
DSEC raw events and labels remain at the canonical 440x640 semantic geometry. Do not add
raw max pooling: the semantic branch begins with a learned standard 5x5 stride-2 PLIF
stem, while a narrow 8-channel native PLIF path preserves thin objects and boundaries.

Use standard spatial/channel convolution for the native detail block, first 32-channel
semantic block, and 32->64 transition. Retain depthwise/pointwise processing deeper in
the network. This improves early cross-channel spatial modelling while keeping the model
near the original weight budget and reducing persistent state relative to naively running
the old full-resolution trunk at 440x640.

Remove the local 96-channel selector, 32-channel native decoder refinement, and spiking
class head. Fuse native semantic32 + detail8 through DW40/PW16 PLIF, then accumulate the
16->11 synaptic current continuously over all ten updates. The loss is still evaluated
once per complete 50 ms record. The continuous readout is stateless between records and
maps to conditional signed weight additions plus integer accumulators on FPGA.

Add a training-only native boundary head with coefficient 0.1 while retaining weighted
CE, 0.2 present-class Dice, and the 0.1 semantic auxiliary CE. Change the DSEC compose
profile to native 440x640 and ten replay chunks to bound the activation graph to one
5 ms update. Keep `artifacts/checkpointsV3/dsec` unchanged, but old v6 checkpoints are
architecturally incompatible and this run must start from scratch.

The new 11-class graph has 142,277 registered parameters, 141,535 executed inference
parameters, 135,624 executed synaptic weights, 27 PLIF populations, 43,366,400 logical
membranes, and 10,982,400 adaptation-enabled states. Dense 16-bit state is 124.61 MiB
before queues/alignment, so the no-DDR sparse-state feasibility gate remains in force.

## 2026-08-23 — Adopt v7 native-resolution state-first graph and migrate RTL to fixed-step Artix-7 baseline

Codex's v7 canonical `EventSpikeSeg140k` is now the sole hardware graph: native 440x640 DSEC input, 27 deployed PLIF populations, 135,624 executed synaptic weights, 43,366,400 membrane states, and a stateless 16->11 temporal class-current readout. The wide 32-channel semantic trunk begins at half resolution after a learned 5x5 stride-2 PLIF stem; the native detail path is only 8 channels. The old 96-channel selector, native decoder refinement, and output class PLIF population are removed.

This revision is accepted as the new state-first architecture because it increases static synaptic weights by about 6.4% relative to v6 while reducing PLIF populations by 27.0%, logical membrane state by about 40.5%, and dense persistent state from about 192.44 MiB to 124.61 MiB even though v7 runs at native 440x640. Hardware architecture search must continue to treat writable neuron state as more expensive than static weight ROM.

## 2026-08-24 — Preserve spike evidence through decoder and native fusion (v8)

The v7 quarter skip used binary OR before a DW->PLIF->PW decoder block, and the native
semantic/detail concatenation also crossed a depthwise PLIF before any channel mixing.
Those intermediate thresholds could discard weak small-object evidence distributed across
encoder, decoder, semantic, and detail channels. Replace quarter OR plus DW/PW refinement
with channel concatenation and one standard 1x1 128->64 PLIF fusion. At the half skip,
retain coincident encoder/decoder events as multiplicity two rather than OR-deduplicating
them. Replace native DW40->PW16 with one standard 3x3 40->16 PLIF so spatial and channel
evidence accumulates jointly before thresholding.

The 11-class graph now has 150,245 registered parameters, 149,503 executed inference
parameters, 143,904 executed synaptic weights, 25 PLIF populations, and 30,976,000 logical
membranes. Threshold-adaptation scope remains 10,982,400 neurons. Compared with v7 this
adds 8,280 static synaptic weights but removes 12,390,400 persistent membrane values and
two PLIF actors. Dense exact membrane/adaptation/24-bit-tag storage falls from 248.68 MiB
to 189.60 MiB. This is accepted as the accuracy/state trade because static ROM growth is
small while fusion becomes less lossy and writable state falls by 28.6%.

The FPGA family is explicitly **AMD/Xilinx Artix-7**, with `XC7A200T-1SBG484C` on Digilent Nexys Video as the reference implementation board. The board DDR3 remains forbidden by the active no-external-memory experiment.

The baseline runtime is fixed-time and identical to training: one 50 ms record contains ten ordered 5 ms steps, executed layer-major. Remove the superseded per-neuron `last_timestamp_us` state and `beta**(delta/5ms)` runtime coefficient path. `plif_update` consumes learned beta directly once per 5 ms step, `sparse_state_bank` stores no timestamp, and `fixed_record_controller` sequences 27 PLIF layers x 10 steps. The final readout accumulates signed current and performs first-index-tie argmax; do not recreate output PLIF/class-spike counting.


## 2026-08-23 — Stream live DSEC in 5 ms bins and preserve touched-neuron lazy state

This supersedes the same-day 50 ms layer-major FPGA scheduling decision while leaving training unchanged. Live camera events are accumulated into consecutive 5 ms ON/OFF bins. One sealed bin must traverse the full deployed graph (27 PLIF actors plus the stateless class-current update) before the bin is retired. Input uses ping-pong buffers so bin `k+1` is captured while bin `k` computes.

The current DSEC training path enables touched-neuron lazy updates. Runtime must therefore preserve that behavior: each live sparse neuron state stores a compact 24-bit `last_bin_tag`; when touched at bin `k`, compute `delta_bins = k - last_bin_tag (mod 2^24)` and apply the learned beta once per elapsed bin before adding current. The first RTL implementation uses an iterative beta multiply so long-idle neurons consume additional cycles; a beta-power LUT/accelerator is allowed later only with bit-exact validation. No 32-bit microsecond timestamp is used.

## 2026-08-24 — Save fixed qualitative DSEC validation previews every epoch

Choose three validation-record indices once from the run seed and reuse those records for
every epoch. Capture their outputs inside the existing chronological validation pass so
recurrent state stays correct and validation does not require extra forward executions.
Save `event | ground truth | prediction` PNG panels under `<checkpoint-dir>/images`.
The event panel collapses all ten 5 ms divisions into the complete 50 ms count map:
polarity 0 is red (negative), polarity 1 is blue (positive), and a shared logarithmic
count scale controls intensity so both low- and high-count pixels remain visible.

The signed 16->11 class-current readout accumulates over a configurable prediction window. Start with ten bins, therefore one prediction every 50 ms / 20 Hz, because that matches training. PLIF/adaptation state continues across prediction boundaries and resets only at sequence/frame gaps.

Define real-time utilization `U = C_bin / (f_clk * 5 ms)` and throughput headroom `H = 1/U`. Sustained operation requires `U <= 1` (`H >= 1`). The starting engineering target is `U <= 0.8` (`H >= 1.25`), leaving 20% timing margin. At 100/150/200 MHz the hard budgets are 500k/750k/1M cycles per bin and the 80% target budgets are 400k/600k/800k cycles. These values must come from measured controller cycle counts after synthesis/RTL integration, not from parameter count.

## 2026-08-25 — Replace the global FPGA scheduler with permanent autonomous ASIC actors

Keep all 25 PLIF populations resident and prohibit runtime layer reconfiguration. A standard
3x3 convolution plane uses nine parallel presynaptic tap projection cells. Each tap applies
the YAML scatter address equation and emits a signed weight contribution; taps do not own
membranes. All contributions for `(layer, output-channel, y, x)` accumulate in one canonical
actor-local current slot and update one actor-local membrane entry.

Preserve the trained 5 ms time semantics with ordered completion tokens. A receiving actor
accepts sparse contributions until its upstream token arrives, commits every touched PLIF
exactly once, emits its spikes, and then forwards completion. This is logically asynchronous
dataflow without a central actor scheduler. The initial VHDL is still a clocked ready/valid
reference; no clockless/QDI claim is made.

Keep VHDL-2008 and replace Vivado for ASIC PPA with GHDL -> Yosys -> OpenROAD. Use ASAP7
only for reproducible predictive 7 nm logic PPA and SKY130RAM only for a manufacturable
tile experiment. Neither is a full-chip tapeout decision. The native graph has 30,976,000
membranes and 189.60 MiB of dense exact state under the current tag/adaptation contract, so
credible full-chip area/power requires characterized high-density SRAM macros and an
accessible 22 nm-or-better foundry PDK. Flip-flop-expanded behavioral arrays are forbidden
as a claimed full-model PPA result.

## 2026-08-25 — Use native SystemVerilog and sequential raw-event ASIC ingress

This supersedes the VHDL/GHDL portion and the ping-pong-bin ingress portion of the preceding
ASIC decision. Implement the ASIC directly in synthesizable SystemVerilog and use
Icarus/cocotb, Yosys, and OpenROAD. Preserve the FPGA attempt in the non-normative
`legacy_fpga_history` section of `project_spec.yaml`, the chronological decision/progress
logs, and Git history.

The ASIC camera interface accepts rectified raw events sequentially in timestamp order.
Each event immediately triggers only its connected static-weight additions; it does not
load a dense 5 ms tensor and does not fetch or update unrelated neuron state. A completion
token is inserted at each trained 5 ms boundary. That token causes each actor to commit
only its touched PLIF destinations once, emit spikes, and forward completion.

Do not threshold or reset a PLIF after every individual signed contribution. Training
performs one PLIF update per 5 ms division after convolutional accumulation, and signed
kernel contributions can cancel. Immediate per-event firing would therefore be a different
event-time neuron model and would require explicit event-driven retraining and accuracy
validation. The current ASIC is sparse and event-sequential in its synaptic work while
retaining the trained 5 ms PLIF commit semantics.

## 2026-08-25 — Treat the 25 ASIC actors as the exact v8 DAG, never as a linear pipeline

`EventSpikeSeg140k` deploys 25 PLIF populations, but their enumeration is only a stable
topological/export order. Runtime interconnect must reproduce the actual model DAG. Input
events fork into `detail_stem` and `stem`; residual blocks binary-OR their bypass and main
spikes; `x1` and `x2` fan out into deeper encoder and later decoder routes; `project3` and
`project2` use 2x nearest-event fanout; decoder concatenations use fixed channel remapping;
`project2 + x1` deliberately preserves coincident events as multiplicity two; semantic and
detail routes converge before `final_fuse.standard`.

Completion tokens follow the same directed routes. A fanout duplicates the tagged token to
every required branch. A multi-input residual/skip/concat node may emit one downstream
completion only after all required upstream tokens for the same 5 ms bin have arrived. This
rendezvous rule is required for correctness: a fast branch must not close a downstream PLIF
epoch before a slower skip/detail branch has contributed.

Use compile-time dedicated routing rather than a programmable NoC unless later evidence
shows programmability is worth its area/energy cost. Actor-local membrane/adaptation SRAM
remains unchanged by this decision; only spikes and completion tokens traverse the graph.
