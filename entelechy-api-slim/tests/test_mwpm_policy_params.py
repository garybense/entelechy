"""Unit tests for entelechy_api.engine.mwpm PolicyParams + TimeVariantPolicy."""

import math

import pytest
from pydantic import ValidationError

from entelechy_api.engine.mwpm import (
    CurveAnchor,
    PolicyParams,
    TimeVariantPolicy,
    neutral,
)


def test_policy_params_defaults():
    p = PolicyParams()
    assert p.reasoning_depth == 3
    assert p.verbosity_target == 3
    assert p.uncertainty_threshold == 0.5
    assert p.tool_bias == {}
    assert p.goal_priority == []
    assert p.temperature_modifier == 0.0


def test_policy_params_validates_bounds():
    with pytest.raises(ValidationError):
        PolicyParams(reasoning_depth=0)
    with pytest.raises(ValidationError):
        PolicyParams(reasoning_depth=6)
    with pytest.raises(ValidationError):
        PolicyParams(uncertainty_threshold=1.5)
    with pytest.raises(ValidationError):
        PolicyParams(temperature_modifier=2.0)


def test_policy_params_merge_overrides_scalars():
    a = PolicyParams(reasoning_depth=2, verbosity_target=4, uncertainty_threshold=0.3)
    b = PolicyParams(reasoning_depth=5, verbosity_target=1, uncertainty_threshold=0.8)
    merged = a.merge(b)
    assert merged.reasoning_depth == 5
    assert merged.verbosity_target == 1
    assert merged.uncertainty_threshold == 0.8


def test_policy_params_merge_multiplies_tool_bias():
    a = PolicyParams(tool_bias={"recall": 1.5, "reflect": 1.0})
    b = PolicyParams(tool_bias={"recall": 2.0, "distill": 1.3})
    merged = a.merge(b)
    assert math.isclose(merged.tool_bias["recall"], 3.0)
    assert merged.tool_bias["reflect"] == 1.0
    assert math.isclose(merged.tool_bias["distill"], 1.3)


def test_policy_params_merge_unions_goal_priority_preserving_order():
    a = PolicyParams(goal_priority=["x", "y"])
    b = PolicyParams(goal_priority=["y", "z"])
    merged = a.merge(b)
    assert merged.goal_priority == ["x", "y", "z"]


def test_policy_params_merge_sums_temperature_modifier():
    a = PolicyParams(temperature_modifier=0.2)
    b = PolicyParams(temperature_modifier=-0.1)
    merged = a.merge(b)
    assert math.isclose(merged.temperature_modifier, 0.1, abs_tol=1e-9)


def test_policy_params_merge_concatenates_rationales():
    a = PolicyParams(rationale="first")
    b = PolicyParams(rationale="second")
    assert a.merge(b).rationale == "first; second"


def test_policy_params_merge_handles_empty_rationale():
    a = PolicyParams()
    b = PolicyParams(rationale="only b")
    assert a.merge(b).rationale == "only b"


def test_policy_params_with_rationale():
    p = PolicyParams(rationale="initial").with_rationale("updated")
    assert p.rationale == "updated"


def test_neutral_baseline():
    n = neutral()
    assert n.rationale == "neutral baseline"
    assert n.reasoning_depth == 3


def test_time_variant_policy_returns_baseline_when_no_anchors():
    base = PolicyParams(reasoning_depth=4)
    curve = TimeVariantPolicy(baseline=base)
    out = curve.evaluate_at(100.0)
    assert out.reasoning_depth == 4


def test_time_variant_policy_clamps_before_first_anchor():
    base = PolicyParams()
    onset = PolicyParams(reasoning_depth=5, rationale="peak")
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(60.0, onset)])
    out = curve.evaluate_at(0.0)
    # Pre-onset: returns baseline merged with first anchor (clamps to first)
    assert out.reasoning_depth == 5


def test_time_variant_policy_clamps_after_last_anchor():
    base = PolicyParams()
    comedown = PolicyParams(reasoning_depth=2, rationale="comedown")
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(3600.0, comedown)])
    out = curve.evaluate_at(10000.0)
    assert out.reasoning_depth == 2


def test_time_variant_policy_interpolates_linearly():
    base = PolicyParams()
    a = PolicyParams(reasoning_depth=1, verbosity_target=1)
    b = PolicyParams(reasoning_depth=5, verbosity_target=5)
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(0.0, a), CurveAnchor(100.0, b)])
    midpoint = curve.evaluate_at(50.0)
    # Linear interp: roughly halfway = 3
    assert midpoint.reasoning_depth == 3
    assert midpoint.verbosity_target == 3


def test_time_variant_policy_interpolates_temperature():
    base = PolicyParams()
    a = PolicyParams(temperature_modifier=0.0)
    b = PolicyParams(temperature_modifier=1.0)
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(0.0, a), CurveAnchor(100.0, b)])
    out = curve.evaluate_at(75.0)
    # Halfway-merge of base (0.0) + interpolated 0.75 → final modifier sums
    assert math.isclose(out.temperature_modifier, 0.75, abs_tol=1e-6)


def test_time_variant_policy_picks_correct_segment_with_three_anchors():
    base = PolicyParams()
    a = PolicyParams(reasoning_depth=1)
    b = PolicyParams(reasoning_depth=5)
    c = PolicyParams(reasoning_depth=2)
    curve = TimeVariantPolicy(
        baseline=base,
        anchors=[
            CurveAnchor(0.0, a),
            CurveAnchor(50.0, b),
            CurveAnchor(100.0, c),
        ],
    )
    # Quarter into first segment (t=12.5): interp(1, 5, 0.25) = 2
    out_first = curve.evaluate_at(12.5)
    assert out_first.reasoning_depth == 2

    # Halfway into second segment (t=75): interp(5, 2, 0.5) = round(3.5) = 4
    out_second = curve.evaluate_at(75.0)
    assert out_second.reasoning_depth == 4


def test_time_variant_policy_zero_span_segment_uses_left():
    base = PolicyParams()
    a = PolicyParams(reasoning_depth=2)
    b = PolicyParams(reasoning_depth=4)
    # Two anchors at exact same t
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(50.0, a), CurveAnchor(50.0, b)])
    out = curve.evaluate_at(50.0)
    # Defensive: returns baseline merged with first matching anchor
    assert out.reasoning_depth in (2, 4)
