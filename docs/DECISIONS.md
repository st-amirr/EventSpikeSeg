# Decisions

## 2026-08-02 — Instruction filename compatibility

The supplied instruction file was named `agent.md`, while the task and common tooling
expect `AGENTS.md`. Preserve `agent.md` as the canonical full text and add a small
`AGENTS.md` pointer. No instructions were discarded.

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

Use one non-negative adaptation scalar per output channel. Each step first decrements
it toward zero, then adds `increment * emitted_spike_count`. This countdown form is
simple to reproduce in fixed-point hardware; per-neuron adaptation remains an ablation.

## 2026-08-02 — Synthetic-first validation

All algorithmic and equivalence work uses deterministic synthetic fixtures before any
FE108 or MEVDT download. Dataset acquisition and measured accuracy are separate future
milestones.
