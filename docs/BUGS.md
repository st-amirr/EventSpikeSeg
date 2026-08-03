# Bugs

## Resolved — Python 3.9 annotation import failure

- Reproduction: collect `tests/test_sparse_conv.py` under Python 3.9.
- Root cause: runtime evaluation of Python 3.10 `X | Y` annotations.
- Fix: postpone annotations in the sparse reference and keep declared Python 3.9 support.
- Regression: the full Python suite collects and passes under Python 3.9.6.

## Resolved — cocotb simulations used one-second precision

- Reproduction: `make rtl-test` initially failed every nanosecond timer.
- Root cause: RTL files omitted a timescale declaration.
- Fix: declare ``timescale 1ns/1ps`` in every unit and use safe pytest IDs/results paths.
- Regression: all five RTL unit simulations pass under Icarus Verilog 13.0.

## Resolved — signed event accumulation saturated positive

- Reproduction: four additions of signed int8 weight `-3` produced `8388601`.
- Root cause: a concatenated sign extension participated in an unsigned expression.
- Fix: explicitly widen both accumulator and weight into signed 25-bit intermediates.
- Regression: cocotb verifies four additions produce `-12`, then clear produces zero.

## Repository hygiene risk — tracked virtual environment

While this run was active, external commit `070fa2d` appeared and included the initial
`.venv` bootstrap files. `.gitignore` now excludes `.venv/` and future generated files,
but removing already tracked environment files requires a deliberate index cleanup in a
subsequent commit; this run did not rewrite or undo the concurrent commit.

## Resolved — non-static VHDL aggregate rejected by GHDL

- Reproduction: `make rtl-test` during the VHDL migration; four units passed and
  `f_inst_top1.vhd` failed elaboration at its minimum-signed-value aggregate.
- Root cause: the aggregate used a variable-derived index together with `others`, which
  GHDL correctly rejected as a non-locally-static mixed choice.
- Fix: initialize all bits to zero and assign the sign bit explicitly.
- Regression: all five VHDL-2008 entities pass GHDL 6.0.0/cocotb.
