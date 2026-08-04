"""Small deterministic surrogate-gradient training smoke test."""

import torch

from .config import EventBinningConfig
from .events import bin_events, synthetic_events
from .system import EventSCNNSystem


def run_smoke_step() -> tuple[float, float]:
    """Run one optimizer step and return loss plus maximum weight change."""

    torch.manual_seed(17)
    binning = EventBinningConfig(width=16, height=16, bin_duration_us=1_000)
    sequence = bin_events(
        synthetic_events(steps=3, x0=3, y0=4),
        binning,
        num_bins=3,
    ).float()
    system = EventSCNNSystem(class_count=2)
    with torch.no_grad():
        for block in system.backbone.blocks:
            block.conv.weight.fill_(1.0)
        system.attention.conv.weight.fill_(1.0)
        system.classification.synapse.weight.fill_(0.1)
    optimizer = torch.optim.SGD(system.parameters(), lr=0.01)
    before = system.backbone.blocks[0].conv.weight.detach().clone()
    outputs = system.trainable_outputs(sequence)
    loss = outputs["attention_spikes"].mean()
    loss = loss + outputs["classification_scores"].square().mean()
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    change = (system.backbone.blocks[0].conv.weight.detach() - before).abs().max()
    if not torch.isfinite(loss) or change <= 0:
        raise RuntimeError("surrogate-gradient smoke step did not update convolution weights")
    return float(loss.detach()), float(change)


def main() -> None:
    loss, change = run_smoke_step()
    print(f"smoke training passed: loss={loss:.8f}, max_weight_change={change:.8f}")


if __name__ == "__main__":
    main()
