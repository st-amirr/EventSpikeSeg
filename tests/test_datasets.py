import numpy as np
import pytest

from eventscnn.datasets import load_event_npz, remap_davis346_coordinate


def test_frozen_davis346_coordinate_mapping() -> None:
    assert remap_davis346_coordinate(0, 0) == (0, 0)
    assert remap_davis346_coordinate(345, 259) == (239, 179)
    with pytest.raises(ValueError):
        remap_davis346_coordinate(346, 0)


def test_tiny_npz_fixture_loads_without_dataset_download(tmp_path) -> None:
    path = tmp_path / "events.npz"
    np.savez(path, t=[0, 999], x=[0, 345], y=[0, 259], p=[0, 1])
    events = load_event_npz(path, remap_davis346=True)
    assert [(event.x, event.y, event.polarity) for event in events] == [
        (0, 0, False),
        (239, 179, True),
    ]


def test_fixture_schema_rejects_missing_arrays(tmp_path) -> None:
    path = tmp_path / "bad.npz"
    np.savez(path, t=[0], x=[0])
    with pytest.raises(ValueError, match="requires arrays"):
        load_event_npz(path)
