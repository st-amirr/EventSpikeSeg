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
DDD17_ARCHITECTURE ?= final_dualpath_wide32
DDD17_MODEL_SUITE ?= final

.PHONY: setup test lint inspect-ddd17 train-ddd17-smoke train-ddd17 benchmark-top-ten benchmark-top-five benchmark-top-three promote-top-three-winner eval-ddd17

setup:
	$(VENV_CREATE)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev,rtl]'

test:
	$(PYTEST) -q

lint:
	$(RUFF) check src tests

inspect-ddd17:
	$(PYTHON) -m eventspikeseg.train inspect --root "$(DDD17_ROOT)"

train-ddd17-smoke:
	$(PYTHON) -m eventspikeseg.train single --root "$(DDD17_ROOT)" \
		--architecture "$(DDD17_ARCHITECTURE)" --suite "$(DDD17_MODEL_SUITE)" --seed $(DDD17_SEED) \
		--epochs 1 --batch-size 1 --time-steps 4 --height 32 --width 32 \
		--train-samples 2 --validation-samples 2 --checkpoint-dir artifacts/checkpoints

train-ddd17:
	$(PYTHON) -m eventspikeseg.train single --root "$(DDD17_ROOT)" \
		--architecture "$(DDD17_ARCHITECTURE)" --suite "$(DDD17_MODEL_SUITE)" --seed $(DDD17_SEED) \
		--epochs 70 --batch-size 1 --time-steps 15 \
		--train-samples 0 --validation-samples 0 --validation-fraction 0.10 \
		--learning-rate 0.001 --checkpoint-every 5 --log-every-batches 1 \
		--checkpoint-dir artifacts/checkpoints

# Historical round-one protocol is intentionally preserved here.
benchmark-top-ten:
	$(PYTHON) -m eventspikeseg.train benchmark --root "$(DDD17_ROOT)" \
		--suite top-ten --seed $(DDD17_SEED) --epochs 10 --batch-size 4 --time-steps 20 \
		--height 64 --width 64 \
		--train-samples 2048 --validation-samples 512 \
		--learning-rate 0.002 --output-dir artifacts/ablation/top_ten

# Completed structural round.
benchmark-top-five:
	$(PYTHON) -m eventspikeseg.train benchmark --root "$(DDD17_ROOT)" \
		--suite top-five --seed $(DDD17_SEED) --epochs 8 --batch-size 14 --time-steps 15 \
		--height 64 --width 64 \
		--train-samples 2048 --validation-samples 512 \
		--learning-rate 0.002 --output-dir artifacts/ablation/top_five

# Completed accuracy-oriented round; retained for reproducibility.
benchmark-top-three:
	$(PYTHON) -m eventspikeseg.train benchmark --root "$(DDD17_ROOT)" \
		--suite top-three --seed $(DDD17_SEED) --epochs 8 --batch-size 14 --time-steps 15 \
		--height 64 --width 64 \
		--train-samples 2048 --validation-samples 512 \
		--learning-rate 0.002 --output-dir artifacts/ablation/top_three

promote-top-three-winner:
	$(PYTHON) -m eventspikeseg.train promote \
		--summary artifacts/ablation/top_three/summary.json \
		--destination artifacts/checkpoints/top_three_winner.pt

eval-ddd17:
	$(PYTHON) -m eventspikeseg.evaluate --root "$(DDD17_ROOT)" \
		--checkpoint artifacts/checkpoints/final_dualpath_wide32_seed17.pt \
		--split test --batch-size 1 --visualizations 8 \
		--visualization-dir artifacts/Validation
