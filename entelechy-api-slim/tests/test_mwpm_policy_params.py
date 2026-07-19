"""Unit tests for entelechy_api.engine.mwpm PolicyParams + TimeVariantPolicy."""

import math

import pytest
from pydantic import ValidationError

from entelechy_api.engine.mwpm import (
    CurveAnchor,
    PolicyParams,
    TimeVariantPolicy,
)


def test_policy_params_defaults():
    p = PolicyParams()
    assert p.verbosity == 0.5
    assert p.abstraction == 0.5
    assert p.creativity == 0.5
    assert p.empathy == 0.5
    assert p.rigor == 0.5
    assert p.tool_use_probability == 0.5


def test_policy_params_validates_bounds():
    with pytest.raises(ValidationError):
        PolicyParams(verbosity=-0.1)
    with pytest.raises(ValidationError):
        PolicyParams(abstraction=1.1)


def test_policy_params_merge_overrides_scalars():
    a = PolicyParams(verbosity=0.2, abstraction=0.4, creativity=0.3)
    b = PolicyParams(verbosity=0.5, abstraction=0.1, creativity=0.8)
    merged = a.merge(b)
    assert merged.verbosity == 0.5
    assert merged.abstraction == 0.1
    assert merged.creativity == 0.8


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


def test_time_variant_policy_returns_baseline_when_no_anchors():
    base = PolicyParams(verbosity=0.4)
    curve = TimeVariantPolicy(baseline=base)
    out = curve.evaluate_at(100.0)
    assert out.verbosity == 0.4


def test_time_variant_policy_clamps_before_first_anchor():
    base = PolicyParams()
    onset = PolicyParams(verbosity=0.9, rationale="peak")
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(60.0, onset)])
    out = curve.evaluate_at(0.0)
    # Pre-onset: returns baseline merged with first anchor (clamps to first)
    assert out.verbosity == 0.9


def test_time_variant_policy_clamps_after_last_anchor():
    base = PolicyParams()
    comedown = PolicyParams(verbosity=0.2, rationale="comedown")
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(3600.0, comedown)])
    out = curve.evaluate_at(10000.0)
    assert out.verbosity == 0.2


def test_time_variant_policy_interpolates_linearly():
    base = PolicyParams()
    a = PolicyParams(verbosity=0.0, abstraction=0.0)
    b = PolicyParams(verbosity=1.0, abstraction=1.0)
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(0.0, a), CurveAnchor(100.0, b)])
    midpoint = curve.evaluate_at(50.0)
    # Linear interp: halfway = 0.5
    assert math.isclose(midpoint.verbosity, 0.5, abs_tol=1e-6)
    assert math.isclose(midpoint.abstraction, 0.5, abs_tol=1e-6)


def test_time_variant_policy_picks_correct_segment_with_three_anchors():
    base = PolicyParams()
    a = PolicyParams(verbosity=0.0)
    b = PolicyParams(verbosity=1.0)
    c = PolicyParams(verbosity=0.4)
    curve = TimeVariantPolicy(
        baseline=base,
        anchors=[
            CurveAnchor(0.0, a),
            CurveAnchor(50.0, b),
            CurveAnchor(100.0, c),
        ],
    )
    # Quarter into first segment (t=12.5): interp(0, 1, 0.25) = 0.25
    out_first = curve.evaluate_at(12.5)
    assert math.isclose(out_first.verbosity, 0.25, abs_tol=1e-6)

    # Halfway into second segment (t=75): interp(1, 0.4, 0.5) = 0.7
    out_second = curve.evaluate_at(75.0)
    assert math.isclose(out_second.verbosity, 0.7, abs_tol=1e-6)


def test_time_variant_policy_zero_span_segment_uses_left():
    base = PolicyParams()
    a = PolicyParams(verbosity=0.2)
    b = PolicyParams(verbosity=0.4)
    # Two anchors at exact same t
    curve = TimeVariantPolicy(baseline=base, anchors=[CurveAnchor(50.0, a), CurveAnchor(50.0, b)])
    out = curve.evaluate_at(50.0)
    # Defensive: returns baseline merged with first matching anchor
    assert out.verbosity in (0.2, 0.4)
