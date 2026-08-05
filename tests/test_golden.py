import json

import numpy as np

from eventscnn.hardware import export_lif_golden_vectors


def test_golden_vectors_are_reproducible_and_describe_order(tmp_path) -> None:
    vector_path, metadata_path = export_lif_golden_vectors(tmp_path)
    first = vector_path.read_bytes()
    export_lif_golden_vectors(tmp_path)
    assert vector_path.read_bytes() == first
    with np.load(vector_path) as vectors:
        assert vectors["spikes"].tolist() == [0, 1, 1, 0]
        assert vectors["membranes"].tolist() == [32, 4, 2767, -32768]
        assert vectors["thresholds"].tolist() == [256, 256, 30000, 256]
    metadata = json.loads(metadata_path.read_text())
    assert metadata["operation_order"][0] == "leak"
    assert metadata["operation_order"][-1] == "homeostasis"
