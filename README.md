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
| Completed detailed analog behavioral forward run | **24.26% mIoU** on one full-resolution frame; matching PyTorch frame: **26.22%** |
| Best-checkpoint pixel accuracy | **66.938%** |
| Final epoch-80 validation mIoU | **27.096%** |
| Input / task | Raw DSEC events, 440 x 640, six merged semantic classes |
| Model size | 149,835 registered parameters; 149,423 after removing auxiliary training heads |
| Inference graph | 25 PLIF populations, 54 directed edges, 143,824 synaptic weights |
| Resident membrane states | 30,976,000 |
| Total logical analog state identities | 54,630,400, including adaptation and class-current state |
| Process / storage | GF180MCU, 180 nm; native MIM capacitors with shared access and update circuits |
| Characterization coverage | 22 module families, 74 retained rows with explicit method and energy boundaries |

The training/validation accuracy rows are **stored PyTorch validation results**. The 24.26%
row is a separate, completed SPICE-calibrated behavioral simulation of one full frame.
It uses detailed per-pulse arithmetic and count/voltage output calibration. Physical
whole-GDS segmentation accuracy remains unqualified. The GDS is a spatially expanded research
assembly; its envelope is not a compact fabricated-die area result. Whole-chip timing,
power, mismatch tolerance, and a full-population 5 ms deadline remain unverified.

## Completed forward simulation

The retained run uses the **best epoch-58 checkpoint**, all **25 actor convolutions**,
one **440 x 640** frame (`zurich_city_02_a`, frame 1), and **10 event bins**. Its result is
**24.26% mIoU**, compared with **26.22% for that same frame in PyTorch**: a difference
of **-1.96 percentage points**. This single-frame comparison is separate from the
234-record software validation summarized below.

The simulation ran on CPU in **14.85 minutes**, with **2.42 GiB peak RSS**. It uses
the nominal **5 fF storage variant**, measured storage/refresh errors, unchanged
**3.3 V supply**, and an assumed **1 mV RMS storage-noise term**. The reported result
uses the detailed per-pulse calibrated model; the later endpoint approximation was
discarded as unnecessary for this forward demonstration.

Start with the [final simulation report](artifacts/analog_asic/evidence/forward_simulation/README.md)
and [comparison image](artifacts/analog_asic/evidence/forward_simulation/comparison/comparison.png).
The directory guide below locates the preserved simulator, outputs, reference and layout.
Calibration/extrapolation limits and unqualified physical categorical/noise behavior
are recorded in the report and completion audit.

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

The completed forward run additionally retains a separate **5 fF compact-bank variant**:
64 cells, native read-bias devices and eight physically routed complementary row drivers
(473 MOS total, **86.2 x 87.9 um**). Its DRC and unique LVS pass, including GDS readback.
The compact bank has its own GDS, Magic source and SPICE netlists in the artifact guide.
The original whole-model GDS still describes the original assembly; full-model layout
replacement/compaction has not been performed.

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
| `artifacts/` | Generated checkpoints, ASIC/analog results, simulation evidence and layouts under the project root |

### Project directory layout

All paths and links below are relative to the main `EventSpikeSeg/` project folder.
Checkpoints, simulation results and layouts are stored together under `artifacts/`.

The project directory tree is:

```text
EventSpikeSeg/
|-- README.md
|-- src/, scripts/, docs/, asic/, article/
`-- artifacts/
    |-- model_checkpoints/dsec_6class/
    |   `-- EventSpikeSeg140k_seed17_best.pt
    |-- ASIC/reports/forward_simulation/
    |   |-- README.md
    |   |-- pytorch_reference.npz
    |   |-- pytorch_reference.png
    |   `-- pytorch_full_validation_summary.json
    `-- analog_asic/
        |-- SIMULATION_RESULTS.md
        |-- layout/EventSpikeSeg140k_GF180_Analog.gds
        |-- components/storage_bank_5ff_driven/
        |   |-- storage_bank_5ff_driven.gds
        |   |-- storage_bank_5ff_driven.mag
        |   |-- storage_bank_5ff_driven.spice
        |   |-- qualification.json
        |   `-- readback/storage_bank_5ff_driven_cap.spice
        `-- evidence/forward_simulation/
            |-- README.md
            |-- result.json
            |-- retention_manifest.json
            |-- final_result/
            |   |-- 0000_zurich_city_02_a_000001.npz
            |   |-- 0000_zurich_city_02_a_000001.png
            |   |-- summary.json
            |   `-- completion_audit.json
            |-- comparison/comparison.png
            `-- provenance/
                |-- count_decoder_full_forward.py
                |-- count_calibrated_mac_provider.py
                |-- completed_forward_arguments.json
                |-- calibrated_convolution_adapter.py
                |-- native_memory_arithmetic_kernel.py
                `-- ... calibration tables and validation records
```

### Artifact file guide

Paths and **Open** links below are relative to the project root.

| File / purpose | Path under `EventSpikeSeg/` | Link |
| --- | --- | --- |
| Main simulator source, preserved byte-for-byte | `artifacts/analog_asic/evidence/forward_simulation/provenance/count_decoder_full_forward.py` | [Open](artifacts/analog_asic/evidence/forward_simulation/provenance/count_decoder_full_forward.py) |
| Count/voltage calibration implementation | `artifacts/analog_asic/evidence/forward_simulation/provenance/count_calibrated_mac_provider.py` | [Open](artifacts/analog_asic/evidence/forward_simulation/provenance/count_calibrated_mac_provider.py) |
| Recorded run arguments | `artifacts/analog_asic/evidence/forward_simulation/provenance/completed_forward_arguments.json` | [Open](artifacts/analog_asic/evidence/forward_simulation/provenance/completed_forward_arguments.json) |
| Final prediction, target, logits and event counts | `artifacts/analog_asic/evidence/forward_simulation/final_result/0000_zurich_city_02_a_000001.npz` | [Open](artifacts/analog_asic/evidence/forward_simulation/final_result/0000_zurich_city_02_a_000001.npz) |
| Final result preview | `artifacts/analog_asic/evidence/forward_simulation/final_result/0000_zurich_city_02_a_000001.png` | [Open](artifacts/analog_asic/evidence/forward_simulation/final_result/0000_zurich_city_02_a_000001.png) |
| Ground truth / reference / simulation comparison | `artifacts/analog_asic/evidence/forward_simulation/comparison/comparison.png` | [Open](artifacts/analog_asic/evidence/forward_simulation/comparison/comparison.png) |
| Final metrics and independent audit | `artifacts/analog_asic/evidence/forward_simulation/final_result/completion_audit.json` | [Open](artifacts/analog_asic/evidence/forward_simulation/final_result/completion_audit.json) |
| Matching PyTorch reference | `artifacts/ASIC/reports/forward_simulation/pytorch_reference.npz` | [Open](artifacts/ASIC/reports/forward_simulation/pytorch_reference.npz) |
| Selected epoch-58 checkpoint | `artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt` | [Open](artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt) |
| Original whole-model layout | `artifacts/analog_asic/layout/EventSpikeSeg140k_GF180_Analog.gds` | [Open](artifacts/analog_asic/layout/EventSpikeSeg140k_GF180_Analog.gds) |
| Final compact 5 fF bank layout | `artifacts/analog_asic/components/storage_bank_5ff_driven/storage_bank_5ff_driven.gds` | [Open](artifacts/analog_asic/components/storage_bank_5ff_driven/storage_bank_5ff_driven.gds) |
| Compact-bank device SPICE netlist | `artifacts/analog_asic/components/storage_bank_5ff_driven/storage_bank_5ff_driven.spice` | [Open](artifacts/analog_asic/components/storage_bank_5ff_driven/storage_bank_5ff_driven.spice) |
| Compact-bank extracted parasitic SPICE netlist | `artifacts/analog_asic/components/storage_bank_5ff_driven/readback/storage_bank_5ff_driven_cap.spice` | [Open](artifacts/analog_asic/components/storage_bank_5ff_driven/readback/storage_bank_5ff_driven_cap.spice) |

The preserved source, parameters and calibration evidence are archived together under
`provenance/`. Cleanup removed the former `artifacts/simulation/` working directory,
its Python environment and raw transient dependencies. Rerunning the archived simulator
requires restoring the environment and restoring/adapting its transient-verification
dependencies and historical paths. The final outputs, source files and layout/netlist
files remain available at the locations above. `retention_manifest.json` records their
original/current locations and checksums.

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

- `article/article.tex` and `article/article.pdf`: the 10-page main manuscript.
- `article/Blocks_figures.tex` and `article/figures/Blocks_figures.pdf`: reusable figures.
- `article/figures/`: layout images and separately exported publication artwork.
- `article/highlights.txt` and `article/publication_manifest.json`: journal upload materials. Captions are embedded in the manuscript and each supplementary PDF.

The 25 layout-region views are separate one-page vector PDFs with matching SVGs
in `article/supplementary_layout/` (Figures S1-S25). Upload individual files;
there is no combined supplementary PDF. Each PDF includes its caption.

The overview simplifies small hierarchy extents. The 25 regional views are supplied as PDF and SVG vectors, using adaptive hierarchy
boundaries and mask geometry. Small cells
use bounds; existing spatial cutoffs remain documented in the vector manifest.
Native device and bank figures provide cell-level detail. Source hashes and rendering settings accompany the figures.

The manuscript is being prepared for **Microelectronics Journal**. The author has
confirmed no specific research funding and no competing interests. Amir Mohammad
Khadem Hosseini performed the research and development; Sattar Mirzakuchaki supervised.
The manuscript discloses AI assistance in software, model development, layout/routing,
simulation workflows and writing. Final co-author approval and submission checks remain.

### Data availability

Project source code and documentation: [EventSpikeSeg on GitHub](https://github.com/st-amirr/EventSpikeSeg).
Only **DSEC**, including its **DSEC-Semantic** labels, was used for the reported experiments:
[dataset downloads](https://dsec.ifi.uzh.ch/dsec-datasets/download/) and
[semantic-label information](https://dsec.ifi.uzh.ch/dsec-semantic/).
Generated checkpoints, GDS and simulation traces are identified by the project manifests;
local ignored artifacts require a separate release to become publicly downloadable.
