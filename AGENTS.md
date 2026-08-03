# EventSCNN-FPGA Agent Instructions

## Mission

Build the system specified in `project_spec.yaml`:

* event-only DAVIS input;
* fixed-duration event timesteps;
* SpikingJelly training;
* three-layer hardware-compatible convolutional SNN;
* custom `f_inst` competition;
* custom `f_long` / `T_thresh` homeostasis;
* region proposals;
* multiclass classification;
* single-object tracking;
* quantized bit-accurate inference;
* independent FPGA RTL implementation.

Spiker+ is not part of the implementation. It may be discussed only as related work and prior inspiration.

Sources of truth

Read these before changing the system:

1. project_spec.yaml
2. AGENTS.md
3. docs/ARCHITECTURE.md, if it exists
4. docs/DECISIONS.md, if it exists
5. The active execution plan under docs/exec-plans/active/, if one exists
6. Tests and executable validation scripts

If required documentation is missing, create it from the YAML specification before implementing major features.

When these disagree, use the YAML specification unless a newer decision is explicitly recorded in `docs/DECISIONS.md`.

Do not silently reinterpret the project specification. Record material deviations and their justification.

## Working method

For every milestone, repeat this loop:

1. Inspect the current repository state.
2. Identify the smallest missing vertical slice.
3. Write or update the active execution plan.
4. Implement only that slice.
5. Add or update tests.
6. Run the relevant validation commands.
7. Inspect failures and logs.
8. Fix root causes rather than suppressing symptoms.
9. Repeat validation until it passes.
10. Update progress, decisions, known limitations, and reproduction instructions.
11. Continue to the next unblocked milestone.

Do not stop merely because the first implementation compiles or one test passes.

Continue until:

* the milestone acceptance criteria pass; or
* a genuine external blocker exists, such as unavailable data, unavailable licensed software, missing physical hardware, or missing credentials.

When blocked, complete all work that does not depend on the blocker and record:

* the exact blocker;
* evidence establishing it;
* what remains;
* the precise command or action required to resume.

## Execution plans

For significant features or refactors, maintain a self-contained execution plan under:

```text
docs/exec-plans/active/
```

The plan must include:

* objective;
* relevant specification sections;
* current repository state;
* assumptions;
* milestones;
* acceptance criteria;
* validation commands;
* progress checklist;
* discoveries;
* decisions;
* unresolved risks;
* next concrete action.

Move completed plans to:

```text
docs/exec-plans/completed/
```

The active plan must always be sufficient for a new Codex session to resume without relying on chat history.

## Progress records

Maintain:

```text
docs/PROGRESS.md
docs/DECISIONS.md
docs/BUGS.md
docs/RESULTS.md
```

`PROGRESS.md` must state what works now, not merely what was attempted.

`DECISIONS.md` must record important architectural decisions and alternatives rejected.

`BUGS.md` must contain reproducible failures, root causes, status, and regression tests.

`RESULTS.md` must contain measured results only. Never invent accuracy, latency, resource use, power, or throughput.

## Architectural constraints

### Input

The canonical software input is:

```text
[T, N, 2, 180, 240]
```

The two channels represent ON and OFF events.

The initial timestep duration is 1 ms, but it must remain configurable.

Multiple events at the same coordinate in one timestep must be represented by an integer event count or equivalent repeated additions.

### SNN backbone

Initial backbone:

```text
Conv 2→8, kernel 5×5, stride 2
LIF + f_inst + f_long

Conv 8→16, kernel 3×3, stride 2
LIF + f_inst + f_long

Conv 16→32, kernel 3×3, stride 2
LIF + f_inst + f_long
```

All convolutions must use:

```text
bias=False
```

Avoid inference-time operations that lack a clear fixed-point FPGA mapping.

### Neuron

The initial neuron must implement a discrete-time hardware-compatible LIF model.

Use a constrained decay:

```text
beta = 1 - 2^(-q)
```

so the FPGA can implement leakage with subtraction and arithmetic shifting.

Use subtractive reset unless an explicitly documented experiment changes it.

The software and RTL order of operations must be identical and documented.

### f_inst

`f_inst` is cross-channel competition among neurons at the same spatial coordinate.

The initial implementation is:

* find candidate output channels above threshold;
* select the channel with the highest candidate membrane;
* permit only that channel to emit a spike;
* optionally decrement competing membrane states by a configurable amount.

Include an ablation where `f_inst` is disabled.

### f_long and T_thresh

The initial hardware-efficient implementation is feature-map-level adaptive thresholding.

Maintain adaptation per output channel rather than per spatial neuron unless running the explicit paper-fidelity ablation.

The implementation must be integer-friendly and deterministic.

### FPGA interpretation

Software training may use dense `Conv2d`.

The hardware backbone must be designed as sparse spike-address accumulation:

```text
active spike
→ shared-kernel weight lookup
→ affected output address generation
→ weight addition to state/current memory
```

Do not flatten convolution into a large fully connected matrix.

Do not describe the FPGA as clockless or fully asynchronous. It is a clocked, sparse, event-addressed implementation of a discrete-time SNN.

## Dataset plan

Primary algorithm dataset:

```text
FE108 with FE240hz annotations
```

Use it for:

* region/objectness supervision;
* multiclass classification;
* single-object tracking.

Map DAVIS346 coordinates to the canonical 240×180 model resolution using a documented deterministic transform.

Hardware-validation dataset:

```text
MEVDT
```

Use it for:

* native DAVIS240C event replay;
* vehicle proposals;
* vehicle tracking;
* FPGA event-rate and throughput analysis.

Before downloading large datasets, implement and test loaders using:

* metadata;
* a tiny fixture;
* synthetic event sequences; or
* a user-provided sample.

Do not commit datasets, generated checkpoints, or large recordings to Git.

## Implementation order

Follow this order unless evidence justifies a documented change:

1. Repository scaffold and reproducible environment.
2. Synthetic event generator and event-bin representation.
3. Hardware-compatible LIF neuron.
4. `f_inst` unit tests.
5. `f_long` / `T_thresh` unit tests.
6. Single convolutional SNN layer.
7. Three-layer backbone.
8. Proposal/objectness output.
9. Classification output.
10. Simple single-object tracking.
11. FE108/FE240hz loader.
12. MEVDT loader.
13. Floating-point training baseline.
14. Quantization and integer reference.
15. Sparse event-scatter software reference.
16. RTL neuron.
17. RTL event-convolution layer.
18. RTL competition and adaptation.
19. Multilayer RTL integration.
20. Dataset replay, synthesis, and measured evaluation.

## Testing requirements

Use fast tests first, then progressively wider validation.

At minimum provide:

* configuration-schema tests;
* event-binning tests;
* neuron-equation tests;
* reset and saturation edge cases;
* `f_inst` winner and tie cases;
* `f_long` rise and decay cases;
* convolution shape and weight-sharing tests;
* state-reset tests;
* deterministic synthetic tracking tests;
* quantized versus floating-point comparison;
* sparse event-scatter versus dense convolution comparison;
* exported golden vectors;
* RTL versus integer-reference comparison when RTL exists.

Use `pytest` for Python tests.

Use type checking and formatting when configured.

Use GHDL and cocotb for RTL verification when available.

If a tool is unavailable, detect that explicitly and provide a documented setup command. Do not mark the corresponding milestone complete.

## Debugging rules

When validation fails:

* reproduce the smallest failing case;
* preserve the failure as a regression test;
* inspect shapes, state reset, timestep ordering, integer rounding, saturation, and threshold/reset ordering;
* compare intermediate layer states;
* do not weaken assertions merely to make tests pass;
* do not introduce unexplained tolerances;
* do not replace failing functionality with placeholders.

For software/RTL mismatches, compare in this order:

1. input event sequence;
2. event counts;
3. convolutional current;
4. pre-threshold membrane;
5. adaptive threshold;
6. candidate spikes;
7. `f_inst` winner;
8. reset membrane;
9. emitted spike addresses.

## Code quality

Prefer:

* small modules;
* explicit tensor shapes;
* typed configuration objects;
* deterministic behavior;
* dependency injection;
* testable pure functions;
* docstrings that describe equations and tensor dimensions;
* configuration-driven architecture;
* reproducible command-line entry points.

Avoid:

* hidden global state;
* hard-coded local paths;
* undocumented tensor transpositions;
* broad exception swallowing;
* placeholder implementations presented as complete;
* premature optimization before correctness;
* hardware code without a bit-accurate software reference.

## Commands

Create a single documented entry point for each operation, such as:

```text
make setup
make test
make lint
make train-smoke
make validate-reference
make rtl-test
```

Equivalent scripts are acceptable when `make` is not appropriate.

Keep `README.md` synchronized with commands that actually work.

## Completion definition

A feature is complete only when:

* implementation exists;
* tests cover normal and edge cases;
* validation passes;
* documentation is updated;
* configuration is reproducible;
* no known silent mismatch remains;
* measured results are recorded where applicable.

At the end of every Codex run, report:

* files changed;
* behavior implemented;
* commands executed;
* passing checks;
* remaining failures;
* active blocker, if any;
* next exact milestone.
