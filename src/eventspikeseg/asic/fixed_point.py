"""Frozen fixed-point arithmetic contract shared by export, reference, and RTL.

The first RTL baseline deliberately uses explicit formats and saturation.  Format
changes are architecture changes: they require regeneration of golden vectors and
semantic-accuracy validation.
"""

from __future__ import annotations

from ..deployment_quantization import ASIC_FORMATS as ASIC_FORMATS
from ..deployment_quantization import FixedFormat as FixedFormat


def round_shift_ties_away(value: int, shift: int) -> int:
    """Arithmetic right shift with deterministic nearest rounding.

    RTL must use the same rule after fixed-point multiplication.  Export uses
    PyTorch's ties-to-even rule only when converting a float coefficient to an
    integer; integer datapath products use this ties-away rule.
    """

    if shift < 0:
        return int(value) << -shift
    if shift == 0:
        return int(value)
    magnitude = abs(int(value))
    rounded = (magnitude + (1 << (shift - 1))) >> shift
    return rounded if value >= 0 else -rounded
