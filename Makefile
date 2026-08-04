PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
MEVDT_ROOT ?= data/mevdt

.PHONY: setup test lint train-smoke train-mevdt-smoke eval-mevdt-smoke validate-reference rtl-test

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev,rtl]'

test:
	$(PYTEST)

lint:
	$(RUFF) check src tests scripts verification/cocotb

train-smoke:
	$(PYTHON) -m eventscnn.smoke_train

train-mevdt-smoke:
	$(PYTHON) -m eventscnn.train_mevdt --root "$(MEVDT_ROOT)" --max-samples 1

eval-mevdt-smoke:
	$(PYTHON) -m eventscnn.evaluate_mevdt --root "$(MEVDT_ROOT)" \
		--checkpoint artifacts/checkpoints/mevdt_attention.pt --max-samples 64

validate-reference:
	$(PYTEST) -q tests/test_quantization.py tests/test_sparse_conv.py

rtl-test:
	$(PYTHON) scripts/run_rtl_tests.py
