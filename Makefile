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
DDD17_ARCHITECTURE ?= EventSpikeSeg
DDD17_MODEL_SUITE ?= final

.PHONY: setup test lint inspect-ddd17 train-ddd17-smoke train-ddd17-140k train-ddd17 train-ddd17-raw eval-ddd17

setup:
	$(VENV_CREATE)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev,rtl]'

test:
	$(PYTEST) -q

lint:
	$(RUFF) check src tests

inspect-ddd17:
	$(PYTHON) -m eventspikeseg.data inspect --root "$(DDD17_ROOT)"

train-ddd17-smoke:
	$(PYTHON) -m eventspikeseg.train single --root "$(DDD17_ROOT)" \
		--architecture EventSpikeSeg140k --suite final --seed $(DDD17_SEED) \
		--input-mode event-bins --epochs 1 --batch-size 1 --time-steps 3 \
		--height 32 --width 32 --train-samples 2 --validation-fraction 0.10 \
		--checkpoint-dir artifacts/checkpoints

train-ddd17-140k:
	$(PYTHON) -m eventspikeseg.train single --root "$(DDD17_ROOT)" \
		--architecture EventSpikeSeg140k --suite final --seed $(DDD17_SEED) \
		--input-mode event-bins --device auto --amp --epochs 80 --batch-size 1 \
		--height 185 --width 320 --accumulate-steps 4 --time-steps 8 \
		--train-samples 0.5 --validation-fraction 0.10 --learning-rate 0.0015 \
		--checkpoint-every 1 --checkpoint-dir artifacts/checkpoints

train-ddd17:
	$(PYTHON) -m eventspikeseg.train single --root "$(DDD17_ROOT)" \
		--architecture "$(DDD17_ARCHITECTURE)" --suite "$(DDD17_MODEL_SUITE)" --seed $(DDD17_SEED) \
		--input-mode event-bins --device auto --amp --epochs 70 --batch-size 1 \
		--height 185 --width 320 --accumulate-steps 4 --time-steps 8 \
		--train-samples 0 --validation-fraction 0.10 --learning-rate 0.001 \
		--checkpoint-every 5 --checkpoint-dir artifacts/checkpoints

train-ddd17-raw:
	$(PYTHON) -m eventspikeseg.train single --root "$(DDD17_ROOT)" \
		--architecture EventSpikeSeg140k --suite final --seed $(DDD17_SEED) \
		--input-mode event-bins --device auto --amp --epochs 80 --batch-size 1 \
		--height 185 --width 320 --accumulate-steps 4 --time-steps 10 \
		--train-samples 0.5 --validation-fraction 0.10 \
		--learning-rate 0.0015 --checkpoint-every 1 --checkpoint-dir artifacts/checkpoints

eval-ddd17:
	$(PYTHON) -m eventspikeseg.evaluate --root "$(DDD17_ROOT)" \
		--checkpoint artifacts/checkpoints/$(DDD17_ARCHITECTURE)_seed$(DDD17_SEED).pt \
		--split test --batch-size 1 --visualizations 8 \
		--visualization-dir artifacts/Validation
