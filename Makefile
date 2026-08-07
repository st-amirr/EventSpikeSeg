ifeq ($(OS),Windows_NT)
PYTHON := .venv/Scripts/python.exe
VENV_CREATE := py -3.11 -m venv .venv
else
PYTHON := .venv/bin/python
VENV_CREATE := python3 -m venv .venv
endif

PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
DDD17_ROOT ?= C:/Users/stamir/Desktop/Dataset/DDD17
DDD17_SEED ?= 17
DDD17_ARCHITECTURE ?= v10_fpga_hybrid
DDD17_MODEL_SUITE ?= final
DDD17_HEIGHT ?= 64
DDD17_WIDTH ?= 64

.PHONY: setup test lint inspect-ddd17 train-ddd17-smoke train-ddd17 benchmark-top-ten benchmark-top-five benchmark-ddd17 promote-winner eval-ddd17

setup:
	$(VENV_CREATE)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev,rtl]'

test:
	$(PYTEST) -q

lint:
	$(RUFF) check src tests

inspect-ddd17:
	$(PYTHON) -m eventscnn.train inspect --root "$(DDD17_ROOT)"

train-ddd17-smoke:
	$(PYTHON) -m eventscnn.train single --root "$(DDD17_ROOT)" \
		--architecture "$(DDD17_ARCHITECTURE)" --suite "$(DDD17_MODEL_SUITE)" --seed $(DDD17_SEED) \
		--epochs 1 --batch-size 1 --time-steps 20 --height $(DDD17_HEIGHT) --width $(DDD17_WIDTH) \
		--train-samples 2 --validation-samples 2 \
		--checkpoint-dir artifacts/checkpoints

train-ddd17:
	$(PYTHON) -m eventscnn.train single --root "$(DDD17_ROOT)" \
		--architecture "$(DDD17_ARCHITECTURE)" --suite "$(DDD17_MODEL_SUITE)" --seed $(DDD17_SEED) \
		--epochs 70 --batch-size 4 --time-steps 20 --height $(DDD17_HEIGHT) --width $(DDD17_WIDTH) \
		--checkpoint-dir artifacts/checkpoints

benchmark-top-ten:
	$(PYTHON) -m eventscnn.train benchmark --root "$(DDD17_ROOT)" \
		--suite top-ten --seed $(DDD17_SEED) --epochs 10 --batch-size 4 --time-steps 20 \
		--height $(DDD17_HEIGHT) --width $(DDD17_WIDTH) \
		--train-samples 2048 --validation-samples 512 \
		--output-dir artifacts/ablation/top_ten

benchmark-top-five:
	$(PYTHON) -m eventscnn.train benchmark --root "$(DDD17_ROOT)" \
		--suite top-five --seed $(DDD17_SEED) --epochs 10 --batch-size 4 --time-steps 20 \
		--height $(DDD17_HEIGHT) --width $(DDD17_WIDTH) \
		--train-samples 2048 --validation-samples 512 \
		--output-dir artifacts/ablation/top_five

benchmark-ddd17: benchmark-top-five

promote-winner:
	$(PYTHON) -m eventscnn.train promote \
		--summary artifacts/ablation/top_five/summary.json \
		--destination artifacts/checkpoints/ddd17_best.pt

eval-ddd17:
	$(PYTHON) -m eventscnn.evaluate --root "$(DDD17_ROOT)" \
		--checkpoint artifacts/checkpoints/ddd17_best.pt \
		--split test --batch-size 4 --visualizations 8 \
		--visualization-dir artifacts/Validation
