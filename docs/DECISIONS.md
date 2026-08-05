# Decisions

## 2026-08-02 — Instruction filename compatibility (superseded)

The supplied instruction file was named `agent.md`, while the task and common tooling
expect `AGENTS.md`. Preserve `agent.md` as the canonical full text and add a small
`AGENTS.md` pointer. No instructions were discarded.

The repository now contains the complete instructions directly in `AGENTS.md`; the
lowercase compatibility arrangement is no longer current.

## 2026-08-02 — Frozen LIF ordering

Use leak → add current → compute effective threshold → candidate comparison → top-1
competition → subtractive reset/loser decrement → emit → homeostasis update. This is
the recommended ordering in the specification and is shared by software, integer
reference, golden vectors, and RTL.

## 2026-08-02 — Deterministic competition

At a tie, the lowest output-channel index wins, matching `argmax` first-index behavior
and a priority encoder in RTL. Competition can be disabled. Loser decrement is applied
only to above-threshold non-winning candidates and is clamped by configured arithmetic.

## 2026-08-02 — Homeostasis rule

Use one non-negative adaptation scalar per output channel. Each floating-point step
first decrements it toward zero, then adds one increment if any neuron in that channel
spiked. This feature-map OR replaced the original spatial mean after the large sparse-map
failure documented below. The countdown form is simple to reproduce in fixed-point
hardware; per-neuron adaptation remains an ablation.

## 2026-08-02 — Synthetic-first validation

All algorithmic and equivalence work uses deterministic synthetic fixtures before any
MEVDT download. Dataset acquisition and measured accuracy are separate milestones.

## 2026-08-03 — VHDL-2008 is the canonical RTL language

All FPGA RTL is VHDL-2008 and portable unit simulation uses GHDL with cocotb. Verilog
and SystemVerilog are not accepted implementation languages. C++ remains optional for
accelerating software references; any HLS use requires a separate evidence-backed
decision and does not replace the canonical VHDL equivalence target.

The earlier SystemVerilog units were executable prototypes created under the previous
“VHDL or SystemVerilog” specification. They are being replaced, not retained as a
parallel implementation, to avoid two divergent RTL sources of truth.

## 2026-08-03 — Existing frameworks are optional and evidence-driven

SpikingJelly remains the primary trainable software framework. FPGA frameworks such as
Spiker+ are permitted and must be evaluated when they may reduce work or risk. Adoption
is component-by-component: a candidate must preserve sparse shared-kernel convolution,
the frozen arithmetic order, custom competition/homeostasis, and system interfaces, and
must pass bit-exact tests. If adaptation is more complex or restrictive than focused
custom VHDL, do not use it. Record the evaluated version, evidence, and outcome before
adding a dependency. No FPGA framework is required merely for the sake of using one.

### Initial Spiker+ evaluation

Reviewed the official repository and paper on 2026-08-03. Spiker+ provides Python-driven
VHDL generation, quantization support, and reusable neuron/accelerator methodology, but
its documented accelerator targets fully connected and recurrent fully connected
architectures. EventSCNN's central datapath is sparse shared-kernel convolution with
event-address scattering, followed by custom competition, homeostasis, proposals, ROI
classification, and tracking. Adopting Spiker+ as the main backend now would therefore
require replacing much of its topology and control structure and would not reduce total
integration risk.

Decision: do not add Spiker+ as a required dependency at this stage. Continue the focused
VHDL convolutional backend, while explicitly re-evaluating isolated Spiker+ neuron,
fixed-point arithmetic, quantization, or test-generation components before implementing
equivalent future modules. No release or commit is pinned until a component is actually
selected. Evidence: [official repository](https://github.com/smilies-polito/Spiker) and
[Spiker+ paper](https://arxiv.org/abs/2401.01141).

## 2026-08-03 — MEVDT vehicle/background training

Use the locally available MEVDT download as the primary real floating-point
vehicle/background dataset. MEVDT CSV timestamps are
nanoseconds, detection text uses absolute XYXY coordinates, and the published
`MEVDT_org_rate_{train,test}.csv` files are authoritative. Train and test sequences must
remain disjoint. APS images are indexing aids only and are not model inputs.

A Finder alias is not a portable dataset path. Commands accept an explicit root and the
local convenience mount is a Git-ignored symbolic link at `data/mevdt`.

The first baseline disables `f_inst` and `f_long`, matching the specification's required
ablation order. Custom dynamics are enabled only after the plain surrogate-gradient
baseline and proposal behavior are sound.

Use positive-weighted mean-squared error on temporal objectness spike rate for this
initial baseline because the head exposes hardware-realizable spikes rather than free
logits. The positive multiplier is 10. This is provisional: held-out proposal metrics,
not training loss, determine whether it is retained or replaced by a focal/logit design.

## 2026-08-03 — Replace box ROI inference with event-supported pixel attention

The 20 ms, stride-8, 1×1 objectness baseline produced fragmented components and zero
held-out recall at IoU 0.5. MEVDT labels arrive at roughly 24 Hz, while measured event
support was much lower in 20 ms than in 50 ms windows. Filled-box targets also ask an
event-only model to activate silent rectangle interiors.

Use 50×1 ms context, keep Conv1/Conv2 stride 2, and change Conv3 to stride 1. Add a
bias-free 3×3 spiking attention head on Conv1. Supervise event-active pixels inside
annotations (with one-pixel half-resolution dilation), pool Conv3 with the model's own
predicted attention, and track weighted centroid/spread. This is the primary path because
it preserves more spatial evidence and has direct convolution, OR-pooling, accumulation,
and moment hardware mappings. Full-resolution attention was rejected for the initial
design because it doubles spatial dimensions and hardware state without matching the
backbone tap. Filled-box objectness and oracle ROI utilities remain diagnostics only.

This redesign does not remove `f_inst`, `f_long/T_thresh`, quantization, sparse scatter,
or VHDL equivalence work. New real-data metrics remain unmeasured until the user runs
training and evaluation; historical box-baseline accuracy is not transferable.

## 2026-08-04 — Window-presence supervision and threshold-calibrated dynamics

The first user-run attention checkpoint was almost silent: positive attention detection
was 28.1% and recall was 0.2%. The loss compared a window-level binary target against a
50-step mean spike rate, where the first possible nonzero value was 0.02 and a target of
1.0 required a spike on every timestep. Replace the mean with differentiable clamped
window spike presence, use 32:1 positive weighting, preserve Conv1 event support with an
auxiliary Dice loss, and regularize only spike rates above 5%. Use fan-in Kaiming
initialization and a hardware-representable threshold of 0.25 (integer 64 at scale 256).

Bounded sampling now uses a seeded shuffle within positive/background classes before
alternation. This avoids selecting only early dataset sequences. MEVDT sequence CSVs are
cached as validated sorted arrays within a process; nanosecond half-open window semantics
are unchanged.

For `f_long`, a spatial mean made one sparse spike vanish as map size grew. Use a
per-channel OR reduction per timestep, which maps to a hardware activity flag. Scale
increment and decay relative to the base threshold: threshold/16 and threshold/32.
Checkpoint metadata freezes these values and evaluation restores them exactly.

Measured selection: keep `f_inst` as the localization/sparsity operating point. It
reduces Conv3 spike rate by about 83% versus the plain shuffled baseline while producing
the best bounded pixel IoU. Keep combined `f_inst + f_long` as a classification-oriented
operating point; it substantially improves classification but reduces localization IoU.

## 2026-08-04 — Fully spiking classification readout

Replace the analog `Linear` classifier with a bias-free synapse matrix feeding one
hardware-compatible LIF neuron per class. At every timestep, max/OR-matched attention
pixels gate Conv3 feature spikes; spatial spike counts drive the class synapses, and the
decision is the argmax of output spike counts. No learned analog logits or inference
softmax remain. During training, class-rate cross-entropy uses a fixed rate scale of four
and does not backpropagate through the attention mask, preventing classification loss
from shrinking the supervised attention support.

Class output neurons use the same power-of-two leak and subtractive-reset contract but
disable `f_inst` and `f_long`. Applying `f_inst` across class neurons was evaluated and
rejected: after a 1,024-step run it starved the vehicle neuron (mean positive class-spike
counts `4.0625` background versus `0.71875` vehicle on a 32-positive diagnostic slice),
leaving classification at `0.5234375`. Independent class integration followed by the
final deterministic argmax reached `0.828125` on the documented 128-frame evaluation.
Centroid moments, argmax/confidence, and alpha-beta tracking remain deterministic digital
post-processing; encoding those bookkeeping operations as neurons would add no useful
spiking computation and would complicate bit-exact hardware.

## 2026-08-04 — Balance future state storage across BRAM and LUTRAM

Do not map every persistent array and queue into BRAM. The current network is dominated
by membrane state rather than weights, so a BRAM-only implementation risks exhausting
block memory even when substantial LUT capacity remains. Use a hybrid, synthesis-guided
hierarchy: large Conv1/Conv2/Conv3 state maps default to BRAM; attention state, quantized
shared weights, short FIFOs, touched-address queues, small current tiles, and lookup
tables are LUTRAM candidates; class state, per-channel homeostasis, counters, and control
remain registers when practical.

This is intentionally not a fixed manual placement. Extra ports may require LUTRAM
replication, and large distributed memories can create routing/timing failures. Compare
BRAM-heavy and balanced synthesis configurations for the chosen device, record packing
and port costs per memory, and select the smallest mapping that meets timing without
changing bit-exact behavior. No utilization improvement is claimed until synthesis is
actually executed.

## 2026-08-04 — Defer EventVOT general-object extension

MEVDT is the sole primary executable dataset. Use EventVOT only as a later event-only
general-object path. EventVOT is deferred until the current MEVDT protocol is stable because multiple
candidate objects require explicit target conditioning. The first implementation must
validate a tiny raw-event fixture and map 1280×720 to 240×180 without distortion by
resizing to 240×135 and padding vertically. No EventVOT result is inferred from MEVDT.

## 2026-08-04 — Sequence-level MEVDT validation before capacity ablations

The earlier 128-frame official-test subset was used repeatedly during development and is
not an untouched test set. Derive a deterministic 20% scene-stratified validation split
from complete official training sequences using partition seed `20260804`, freeze the
exact train/validation sequence lists in each checkpoint, and evaluate records in
chronological order. Use seeds `17`, `101`, and `2026`; select only on validation and
reserve the official test split until the configuration is frozen.

The required report is tracking success AUC, center precision@20, HOTA, MOTA, IDF1,
classification F1, and pixel-attention IoU. Only after those three runs may capacity be
added, in this order and only for a diagnosed deficiency: multiscale Conv1/Conv2/Conv3
spike fusion, a depthwise-separable spiking refinement block, adjacent-sample temporal
attention supervision, then a fourth downsampled Conv-LIF layer if semantic
classification remains inadequate. `f_inst` and `f_long/T_thresh` remain available.

## 2026-08-04 - Use a CPU-only Docker Compose environment across hosts

Use one Python 3.11 Debian image for Python tests, training/evaluation, quantized
reference checks, and GHDL/cocotb RTL tests. Mount source read-only and persist only
ignored checkpoints to the host. Import MEVDT into an optional named Docker volume for
training because direct Windows/macOS CSV bind mounts are too slow for this loader.

Do not retain CUDA dependencies for the current trainer. A measured two-sample probe was
substantially slower on CUDA because the model executes many small operations across 50
sequential timesteps; the CUDA image and experimental device-routing code were removed.
Reconsider GPU execution only after batching or timestep vectorization is implemented
and benchmarked. The CPU container remains architecture-portable through Docker Desktop.

## 2026-08-04 — Make MEVDT the sole primary dataset

MEVDT is the only primary dataset for training, deterministic validation, tracking
evaluation, and native-resolution FPGA replay. Its learned classification contract is
vehicle versus background; no unsupported multiclass claim is part of the current
project. EventVOT remains a separately deferred general-object extension.

Zero classification F1, HOTA, or tracking success AUC is a benchmark regression. The
full evaluation command must fail its acceptance gate and return the active milestone to
the documented diagnosis/fix/retrain loop instead of allowing work to advance silently.

## 2026-08-04 — Scale classification synaptic current by an exact power of two

Apply a five-bit right-shift equivalent (divide by 32) between the bias-free class
synapses and independent output LIF neurons. Seed-101 traces showed both outputs
saturating near the 50-timestep spike ceiling because unscaled currents exceeded the
`0.25` threshold by orders of magnitude. A 1,024-sample repaired checkpoint passed the
complete-validation nonzero gate with classification F1 `0.918100`, HOTA `0.328636`, and
tracking success AUC `0.398309`.

This preserves spike-count decoding, introduces no bias or analog classifier, and maps
directly to fixed-point arithmetic. Threshold retuning and output competition were
rejected because they either obscure the excessive-current cause or reintroduce the
previously measured cross-class starvation failure.

## 2026-08-04 — Do not adopt three attention-spread units globally

A training-only sweep favored `3 × spread_x/y` over the original scale 4. On held-out
seed 2026 it improved HOTA from `0.474080` to `0.485307`, but on repaired seed 101 it
reduced HOTA from `0.469137` to `0.461110`. Several secondary seed-101 metrics improved,
including MOTA, IDF1, and center precision, so scale 3 remains a useful ablation but is
not a universal HOTA improvement.

Retain scale 4 as the global default until all three repaired seeds are available. Do
not freeze a decoder scale from one seed when the cross-seed HOTA direction changes.

## Single-file neural model source

**Decision:** Keep the complete neural model in `src/eventscnn/model.py`.

**Reason:** The previous split across `dynamics.py`, `models.py`, `heads.py`, and
`system.py` obscured the end-to-end architecture and retained overlapping current and
compatibility interfaces. A single source makes the full spiking path reviewable while
leaving dataset, tracking, metrics, quantization, sparse reference, and RTL concerns
separate.

**Migration:** All repository imports and tests were changed to use `eventscnn.model`,
after which the four previous modules were deleted. They must not be recreated. Existing
state-dict checkpoint keys are unaffected because module attributes inside
`EventSCNNSystem` were preserved; only Python import paths changed.
