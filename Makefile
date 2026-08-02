PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff

.PHONY: setup test lint train-smoke validate-reference rtl-test

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev,rtl]'

test:
	$(PYTEST)

lint:
	$(RUFF) check src tests

train-smoke:
	$(PYTHON) -m eventscnn.smoke_train

validate-reference:
	$(PYTEST) -q tests/test_quantization.py tests/test_sparse_conv.py

rtl-test:
	$(PYTHON) scripts/run_rtl_tests.py
