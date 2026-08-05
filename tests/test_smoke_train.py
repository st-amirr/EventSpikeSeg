from eventscnn.train import run_smoke_step


def test_surrogate_gradient_updates_shared_convolution_weights() -> None:
    loss, change = run_smoke_step()
    assert loss > 0
    assert change > 0
