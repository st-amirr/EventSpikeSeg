from dataclasses import replace

import pytest

from eventscnn.evaluate_mevdt import MEVDTEvaluationResult, require_nonzero_core_metrics


def _passing_result() -> MEVDTEvaluationResult:
    values = {
        field: 1 if field in {"sequences", "samples", "positive_samples"} else 0.1
        for field in MEVDTEvaluationResult.__dataclass_fields__
    }
    values.update(
        evaluation_split="validation",
        complete_sequences=True,
        negative_samples=0,
        tracking_ground_truth_detections=1,
        tracking_predicted_detections=1,
    )
    return MEVDTEvaluationResult(**values)


def test_core_metric_gate_accepts_nonzero_classification_and_tracking() -> None:
    require_nonzero_core_metrics(_passing_result())


@pytest.mark.parametrize("metric", ["classification_f1", "hota", "tracking_success_auc"])
def test_core_metric_gate_routes_zero_result_back_to_bug_loop(metric: str) -> None:
    result = replace(_passing_result(), **{metric: 0.0})
    with pytest.raises(RuntimeError, match=metric):
        require_nonzero_core_metrics(result)
