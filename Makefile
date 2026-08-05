ifeq ($(OS),Windows_NT)
PYTHON := .venv/Scripts/python.exe
VENV_CREATE := py -3.11 -m venv .venv
else
PYTHON := .venv/bin/python
VENV_CREATE := python3 -m venv .venv
endif

PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
MEVDT_ROOT ?= data/mevdt

.PHONY: setup test lint train-smoke train-mevdt-smoke eval-mevdt-smoke validate-reference rtl-test rtl-test-docker

setup:
	$(VENV_CREATE)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev,rtl]'

test:
	$(PYTEST)

lint:
	$(RUFF) check src tests scripts verification/cocotb

train-smoke:
	$(PYTHON) -m eventscnn.train --smoke

train-mevdt-smoke:
	$(PYTHON) -m eventscnn.train --root "$(MEVDT_ROOT)" --max-samples 2 \
		--checkpoint artifacts/checkpoints/mevdt_smoke.pt

eval-mevdt-smoke: train-mevdt-smoke
	$(PYTHON) -m eventscnn.evaluate --root "$(MEVDT_ROOT)" \
		--checkpoint artifacts/checkpoints/mevdt_smoke.pt --split validation --max-samples 2

validate-reference:
	$(PYTEST) -q tests/test_quantization.py tests/test_sparse_conv.py

rtl-test:
	$(PYTHON) scripts/run_rtl_tests.py

rtl-test-docker:
	docker compose run --build --rm rtl-test
