# Decisions

## 2026-08-05 — Reset from MEVDT tracking to DDD17 segmentation

Tracking, box decoding, alpha-beta tracking, global classification, and MEVDT metrics are inactive. The task is six-class semantic segmentation using the Ev-SegNet DDD17 representation.

## 2026-08-05 — Preserve the six event-statistic channels

The six channels are polarity histogram, timestamp mean, and timestamp standard deviation pairs. They are repeated as direct current over internal SNN steps and are not reinterpreted as chronological bins.

## 2026-08-06 — Preserve the completed ten-model experiment separately

Round one completed with `v10_fpga_hybrid` highest at mIoU 0.3130. The complete preset registry is moved to `top_ten_models.py`; it remains reproducible but is no longer part of the canonical production module.

## 2026-08-06 — Keep model.py canonical-only

`model.py` contains one architecture interface. It currently installs the measured round-one incumbent. Experimental architectures belong in explicit experiment files and may not be added back to `model.py`.

## 2026-08-06 — Run a spike-native top-five round

The second round tests combinations derived from v10, v03, v02, and v08 using PLIF, feature-map `f_long`, explicit `T_thresh`, and selected hidden-layer `f_inst`. Ordinary BN and GAP gating are not included because this round targets mechanisms that remain meaningful during neuromorphic inference.

## 2026-08-06 — Do not enable f_inst in every contender

Cross-channel winner-take-all may improve sparsity but can remove simultaneous semantic features. It is therefore isolated to two of five contenders rather than treated as automatically beneficial.

## 2026-08-06 — Treat PLIF as trainable, not yet hardware-exact

PLIF learns continuous per-channel retention. The eventual FPGA model must quantize it to an integer-friendly leak, then run accuracy and bit-exact regression tests before PLIF can be claimed as deployed.

## 2026-08-06 — Round-one zero-IoU classes are an open data/training issue

Object and human class performance cannot be solved by architecture ranking alone. Before final selection, record class pixel counts, image-presence counts, prediction counts, and confusion matrices at the benchmark resolution.

## 2026-08-07 — Reject the first PLIF/homeostasis top five as final models

The first round-two winner reached only mIoU 0.2464 versus the incumbent 0.3130, and the lightweight `f04` emitted zero output spikes. Preserve the definitions/checkpoints for diagnosis but do not promote them.

## 2026-08-07 — Replace fixed T_thresh with learnable continuous adaptation persistence

A discrete integer hold timer cannot receive useful gradients through standard backpropagation. Revised rate homeostasis learns a bounded continuous `tau`, with retention `exp(-1/tau)`, plus per-channel adaptation strength and target firing rate. Quantize these only after architecture selection.

## 2026-08-07 — Make homeostasis bidirectional and rate-based

Use spatial mean spike rate instead of feature-map `amax`. Threshold adaptation may become negative for silent channels and positive for overactive channels, bounded around the learnable base threshold.

## 2026-08-07 — Remove hard class-head WTA from revised contenders

Independent output class neurons accumulate spikes and compete only through final temporal argmax. This preserves a fully spiking learned output while allowing gradients to reach rare classes.

## 2026-08-07 — Restrict f_inst rather than apply it globally

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

Keep PyTorch as the tensor/autograd/optimizer substrate, but require SpikingJelly public `activation_based` components for learned synaptic stages. `SpikingStage` uses the SpikingJelly `Conv2d` synapse layer, and `ParametricLIF` delegates its charge equation to SpikingJelly `ParametricLIFNode`. Preserve the already-benchmarked per-channel beta by feeding a per-channel reciprocal-tau tensor into the SpikingJelly PLIF charge equation. Custom dynamic threshold, `peer_membrane` fInst, triangular fLong/TThresh, reset ordering, and hardware-visible state remain explicit project code. There is no conventional PyTorch Conv2d model fallback.

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
- PLIF, learnable threshold, stem-only peer-membrane fInst, encoder/context triangular fLong;
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


## 2026-08-09 — Restrict canonical fLong to semantic encoder/context

Decision: introduce a canonical-only `encoder_context` fLong scope. Historical `encoder` scope semantics remain unchanged. The final model no longer applies triangular fLong to the full-resolution stem/x1, custom detail branch, or auxiliary head; fLong begins at x2 after the first spatial downsampling and remains active through x2/x3/context. This matches the intended architecture and removes unnecessary per-pixel temporal state without reducing channels, T, precision, or gradient horizon. Final parameter count becomes 237,597. Stateless convolution plus affine current transforms are vectorized across the T×N batch dimension while PLIF/LIF updates remain sequential, preserving identical temporal dynamics and gradients. The training output contract also uses scalar activity rates instead of retaining complete hidden spike sequences.


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
for each chunk immediately, preserve PLIF membrane/homeostasis values, and detach
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

Nontrivial RTL items are the stem peer-membrane fInst rule, triangular fLong/TThresh
adaptation, and the selector's global binary channel enable. The selector `amax(H,W)` can
be implemented efficiently as a per-channel any-spike flag because selector outputs are
binary. Do not silently remove any of these mechanisms; approximations require
revalidation/fine-tuning.

Verification proceeds from SpikingJelly float to a bit-exact integer reference, VHDL RTL
simulation, Vivado synthesis/place-and-route, post-implementation timing simulation, and
representative-event SAIF/VCD power analysis. These Vivado results are estimates. Only
instrumented ZCU104 results may be called measured hardware power/latency.
