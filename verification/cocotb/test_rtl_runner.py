from pathlib import Path

import pytest
from cocotb.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("top", "sources", "test_module", "parameters"),
    [
        ("plif_update", ["asic/rtl/plif_update.sv"], "test_plif_update", {}),
        (
            "presynaptic_tap_array",
            ["asic/rtl/presynaptic_tap_array.sv"],
            "test_presynaptic_tap_array",
            {},
        ),
        (
            "asynchronous_plif_actor",
            ["asic/rtl/plif_update.sv", "asic/rtl/asynchronous_plif_actor.sv"],
            "test_asynchronous_plif_actor",
            {},
        ),
        (
            "convolution_plif_actor",
            [
                "asic/rtl/presynaptic_tap_array.sv",
                "asic/rtl/plif_update.sv",
                "asic/rtl/asynchronous_plif_actor.sv",
                "asic/rtl/convolution_plif_actor.sv",
            ],
            "test_convolution_plif_actor",
            {"KERNEL_WEIGHTS": sum(20 << (8 * tap) for tap in range(9))},
        ),
        (
            "peer_membrane_inhibition",
            ["asic/rtl/peer_membrane_inhibition.sv"],
            "test_peer_membrane_inhibition",
            {},
        ),
        (
            "triangular_threshold_adaptation",
            ["asic/rtl/triangular_threshold_adaptation.sv"],
            "test_triangular_threshold_adaptation",
            {},
        ),
        ("class_argmax", ["asic/rtl/class_argmax.sv"], "test_class_argmax", {}),
        (
            "class_current_update",
            ["asic/rtl/class_current_update.sv"],
            "test_class_current_update",
            {},
        ),
    ],
    ids=[
        "plif_update",
        "presynaptic_tap_array",
        "asynchronous_plif_actor",
        "convolution_plif_actor",
        "peer_membrane_inhibition",
        "triangular_threshold_adaptation",
        "class_argmax",
        "class_current_update",
    ],
)
def test_asic_rtl(
    top: str,
    sources: list[str],
    test_module: str,
    parameters: dict[str, int],
    tmp_path: Path,
) -> None:
    runner = get_runner("icarus")
    runner.build(
        verilog_sources=[ROOT / item for item in sources],
        hdl_toplevel=top,
        build_dir=tmp_path / top,
        always=True,
        build_args=["-g2012"],
        parameters=parameters,
    )
    runner.test(
        hdl_toplevel=top,
        test_module=test_module,
        test_dir=tmp_path / top,
    )
