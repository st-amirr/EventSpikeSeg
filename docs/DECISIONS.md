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
first decrements it toward zero, then adds `increment * mean_emitted_spike_rate`; the
integer reference accepts an explicit channel spike count and scaled increment. This countdown form is
simple to reproduce in fixed-point hardware; per-neuron adaptation remains an ablation.

## 2026-08-02 — Synthetic-first validation

All algorithmic and equivalence work uses deterministic synthetic fixtures before any
FE108 or MEVDT download. Dataset acquisition and measured accuracy are separate future
milestones.

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

## 2026-08-03 — MEVDT-first binary training while FE108 access is blocked

Keep FE108 as the multiclass target, but use the locally available MEVDT download for
the first real floating-point vehicle/background baseline. MEVDT CSV timestamps are
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
