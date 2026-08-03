"""Deterministic golden-vector generation for Python/RTL equivalence."""

import json
from pathlib import Path

import numpy as np
import torch

from .quantization import integer_lif_step


def export_lif_golden_vectors(directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    currents = torch.tensor([32, 230, 40_000, -40_000], dtype=torch.int64)
    thresholds = torch.tensor([256, 256, 30_000, 256], dtype=torch.int64)
    adaptation = torch.tensor([0], dtype=torch.int64)
    membrane = torch.zeros((1, 1, 1, 1), dtype=torch.int64)
    membranes = []
    spikes = []
    for value, threshold_value in zip(currents, thresholds):
        membrane, spike = integer_lif_step(
            membrane,
            value.reshape(1, 1, 1, 1),
            threshold=threshold_value.reshape(1),
            adaptation=adaptation,
            beta_shift=4,
            competition=False,
        )
        membranes.append(int(membrane.item()))
        spikes.append(int(spike.item()))
    vector_path = directory / "golden_lif_vectors.npz"
    np.savez(
        vector_path,
        currents=currents.numpy(),
        thresholds=thresholds.numpy(),
        membranes=np.asarray(membranes),
        spikes=np.asarray(spikes),
    )
    metadata_path = directory / "golden_lif_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "operation_order": [
                    "leak",
                    "add_current",
                    "saturate_membrane",
                    "compare_threshold",
                    "competition",
                    "subtractive_reset",
                    "emit",
                    "homeostasis",
                ],
                "beta_shift": 4,
                "threshold": "per_step",
                "membrane_bits": 16,
            },
            indent=2,
        )
        + "\n"
    )
    return vector_path, metadata_path
