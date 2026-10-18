# EventSpikeSeg

**Analog/Mixed-Signal ASIC Implementation of an Event-Camera Spiking Segmentation Network**

EventSpikeSeg combines a compact PyTorch spiking segmentation model with a GF180MCU
180 nm analog/mixed-signal research implementation. The delivered hardware work includes
a full hierarchical GDS assembly and representative module power/energy characterization.
The repository contains model/training code, circuit and control sources, documentation,
and manuscript material for **Microelectronics Journal**.

The implemented model is **EventSpikeSeg140k**: a spiking encoder/decoder with a native
spatial-detail branch, learnable parametric LIF (PLIF) neurons, and six continuous
class-current outputs. Original floating-point parameters supply the analog reference;
quantization-aware training is not required for this analog mapping.

## Results at a glance

| Item | Retained result |
| --- | --- |
| Best software validation mIoU | **27.976%**, seed 17, epoch 58 of 80 |
| Best-checkpoint pixel accuracy | **66.938%** |
| Final epoch-80 validation mIoU | **27.096%** |
| Input / task | Raw DSEC events, 440 x 640, six merged semantic classes |
| Model size | 149,835 registered parameters; 149,423 after removing auxiliary training heads |
| Inference graph | 25 PLIF populations, 54 directed edges, 143,824 synaptic weights |
| Resident membrane states | 30,976,000 |
| Total logical analog state identities | 54,630,400, including adaptation and class-current state |
| Process / storage | GF180MCU, 180 nm; native MIM capacitors with shared access and update circuits |
| Characterization coverage | 22 module families, 74 retained rows with explicit method and energy boundaries |

These accuracy values are **stored PyTorch validation results**. The physical implementation
has not been evaluated for segmentation mIoU. The GDS is a spatially expanded research
assembly; its envelope is not a compact fabricated-die area result. Whole-chip timing,
power, mismatch tolerance, and a full-population 5 ms deadline remain unverified.

## Checkpoint accuracy and provenance

The epoch-80 checkpoint, `EventSpikeSeg140k_seed17_epoch080.pt`, records both its own
validation metrics and the best metrics reached during training. Its final weights score
**27.096% mIoU**; its `best_mean_iou` field is
`0.27976271510124207`, achieved at **epoch 58**. The selected
`EventSpikeSeg140k_seed17_best.pt` contains that epoch-58 state and is the source of the
floating-point analog reference.

Checkpoints are retained locally under `artifacts/model_checkpoints/dsec_6class/`.
The small, tracked [checkpoint metrics record](docs/checkpoint_metrics.json) includes
file hashes, final and best metrics, class names, and the recorded validation protocol.
No new evaluation was run to produce this summary.

The recorded split uses **zurich_city_02_a**, 234 validation records, seven training
sequences, seed 17, and six merged classes. Each 50 ms record contains ten chronological
5 ms model updates. These results apply to this recorded validation split; they are not
an official DSEC test-set or eleven-class benchmark score.

Best-checkpoint per-class validation IoU:

| Merged class | IoU (%) |
| --- | ---: |
| flat | 82.454 |
| construction+sky | 39.400 |
| object | 6.775 |
| nature | 29.189 |
| human | 1.209 |
| vehicle | 8.830 |

The low rare-class IoUs are retained explicitly. The manuscript already reports the
27.976% software result separately from circuit characterization.

## Analog/mixed-signal implementation

A presynaptic spike triggers a signed weighted charge contribution. Pulse duration and
injection circuitry encode the contribution; the weight does not set the presynaptic
firing frequency. Contributions accumulate within each 5 ms model bin before the
model-defined PLIF leak, threshold, reset, inhibition, and adaptation operations.

Membrane values reside in native capacitor cells. A 64-state bank combines three-transistor
access/sensing cells with nominal 50 fF MIM storage; readers, bias, update circuits, and
digital event/address control are shared across states. Six continuous class-current
accumulators implement the readout. Full-precision training does not establish the
precision attained by the analog circuits.

Representative nominal results include a **41.711 uW** biased PLIF core and **0.531 mV**
selected-state drift over a 5 ms hold. Their operating windows and measurement boundaries
are documented in [RESULTS](docs/RESULTS.md) and the manuscript. Module measurements
and shared estimates overlap and must not be summed into a full-chip power claim.
Reported circuit results are simulation-derived; no fabricated-chip measurements are claimed.

Historical fixed-point exporters, digital RTL, ASAP7 work, and the larger XL model remain
as development/reproducibility references. The active article implementation uses GF180
analog state and the original float checkpoint.

## Repository guide

| Location | Contents |
| --- | --- |
| `src/eventspikeseg/model.py` | EventSpikeSeg140k and XL model definitions |
| `src/eventspikeseg/model_components.py` | Shared PLIF, convolution, and SNN primitives |
| `src/eventspikeseg/train.py` | Training and chronological validation engine |
| `src/eventspikeseg/data.py` | DDD17 and raw-event DSEC loading |
| `src/eventspikeseg/asic/` | Retained export and hardware reference utilities |
| `asic/analog/` | Analog/mixed-signal circuit and control sources |
| `scripts/` | Export, characterization, layout, and figure utilities |
| `docs/project_spec.yaml` | Current implementation inventory and evidence boundaries |
| `docs/checkpoint_metrics.json` | Verified best/final checkpoint metrics and hashes |
| `docs/ARCHITECTURE.md` | Model and runtime design details |
| `docs/RESULTS.md` | Retained software and implementation results |
| `docs/ACTIVE_TASKS.md` | Current scope and remaining author actions |
| `article/` | Local manuscript sources, figures, and submission package |
| `artifacts/` | Large local checkpoints, GDS, traces, and generated evidence; ignored by Git |

The article directory has its own Git history. Manuscript paths refer to the local
checkout; availability on GitHub depends on publishing that directory/repository as well.
Start with the current entries in `docs/ACTIVE_TASKS.md` and `docs/project_spec.yaml`;
dated digital and earlier-process entries are historical.

## Software setup

Use **Python 3.9-3.12**. The declared dependencies include PyTorch 2.0-2.2 and
SpikingJelly 0.0.0.0.14; see [pyproject.toml](pyproject.toml).

```bash
git clone https://github.com/st-amirr/EventSpikeSeg.git
cd EventSpikeSeg
python -m venv .venv
# Activate .venv with the command for your shell.
python -m pip install -e ".[dev,rtl]"
python -m eventspikeseg.train --help
```

Obtain DSEC-Semantic or DDD17 separately and configure dataset paths before training.
The default six-class DSEC mapping merges road/sidewalk, construction/sky,
poles/signs, vegetation, humans, and vehicles. Dataset files and checkpoints are not
included in the Git repository.

[compose.yaml](compose.yaml) supplies GPU training/data-inspection services;
[compose_ASIC.yaml](compose_ASIC.yaml) supplies the CPU verification environment.
Set `EVENTSPIKESEG_ARTIFACTS_DIR` in a local `.env` file to your artifact directory.
Existing Compose training commands are saved resume experiments: inspect checkpoint,
dataset, and QAT arguments before starting them. The retained analog flow uses float
parameters and does not require those historical QAT settings.

```bash
docker compose run --rm inspect-dsec
docker compose -f compose_ASIC.yaml run --rm test
```

These commands are entry points for local setup/verification, not a claim that the
full analog implementation has passed end-to-end model equivalence.

## Manuscript and layout figures

Local publication material includes:

- `article/article.tex` and `article/article.pdf`: the 10-page manuscript.
- `article/Blocks_figures.tex` and `article/figures/Blocks_figures.pdf`: reusable figures.
- `article/submission/Supplementary_layout_sections.pdf`: 25 GDS-derived actor-region views,
  keyed to numbered locations in the complete layout overview.
- `article/submission/`: editable sources, separate artwork, captions, highlights, and manifest.

The overview simplifies small hierarchy extents. The regional views show eight hierarchy
levels, with deeper cells represented by bounds; native device and bank figures provide
cell-level detail. Source hashes and rendering settings accompany the figures.

The manuscript is being prepared for **Microelectronics Journal**. Author declarations,
final author approval, and a public research-data deposit/citation or justified access
restriction remain required before submission. A GitHub source repository alone does
not make the ignored checkpoints, GDS, and simulation evidence publicly available.
