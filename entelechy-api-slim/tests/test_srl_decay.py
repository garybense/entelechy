"""Unit tests for entelechy_api.engine.srl.decay — pure functions, no fixtures."""

import math

import pytest

from entelechy_api.engine.srl.decay import (
    apply_decay,
    exponential_decay,
    half_life_decay,
    linear_floor_decay,
    safe_age_seconds,
)


def test_exponential_decay_at_zero_age_preserves_score():
    out = exponential_decay([("a", 1.0, 0.0)], half_life_seconds=3600)
    assert out == [("a", 1.0)]


def test_exponential_decay_halves_at_half_life():
    out = exponential_decay([("a", 1.0, 3600)], half_life_seconds=3600)
    assert out[0][0] == "a"
    assert math.isclose(out[0][1], 0.5, rel_tol=1e-9)


def test_exponential_decay_quarters_at_two_half_lives():
    out = exponential_decay([("a", 1.0, 7200)], half_life_seconds=3600)
    assert math.isclose(out[0][1], 0.25, rel_tol=1e-9)


def test_exponential_decay_negative_age_is_clamped():
    out = exponential_decay([("a", 1.0, -1000)], half_life_seconds=3600)
    assert math.isclose(out[0][1], 1.0, rel_tol=1e-9)


def test_exponential_decay_sorts_descending():
    items = [("old", 1.0, 7200), ("new", 1.0, 0), ("mid", 1.0, 3600)]
    out = exponential_decay(items, half_life_seconds=3600)
    assert [k for k, _ in out] == ["new", "mid", "old"]


def test_exponential_decay_rejects_nonpositive_half_life():
    with pytest.raises(ValueError):
        exponential_decay([("a", 1.0, 0)], half_life_seconds=0)


def test_half_life_decay_respects_floor():
    out = half_life_decay([("a", 1.0, 1_000_000_000)], half_life_seconds=3600, floor=0.1)
    assert math.isclose(out[0][1], 0.1, rel_tol=1e-9)


def test_half_life_decay_floor_validation():
    with pytest.raises(ValueError):
        half_life_decay([("a", 1.0, 100)], floor=1.5)


def test_linear_floor_decay_full_weight_band():
    out = linear_floor_decay([("a", 1.0, 1000)], full_weight_seconds=3600, zero_weight_seconds=86400, floor=0.1)
    assert math.isclose(out[0][1], 1.0, rel_tol=1e-9)


def test_linear_floor_decay_zero_weight_band_uses_floor():
    out = linear_floor_decay([("a", 1.0, 100_000)], full_weight_seconds=3600, zero_weight_seconds=86400, floor=0.1)
    assert math.isclose(out[0][1], 0.1, rel_tol=1e-9)


def test_linear_floor_decay_interpolates_in_band():
    # Halfway through the decay span
    out = linear_floor_decay(
        [("a", 1.0, 45000)],  # midpoint between 3600 and 86400 (~45000)
        full_weight_seconds=3600,
        zero_weight_seconds=86400,
        floor=0.0,
    )
    # Should be ~0.5 since floor is 0 and we're roughly halfway
    assert 0.4 < out[0][1] < 0.6


def test_linear_floor_decay_validates_bounds():
    with pytest.raises(ValueError):
        linear_floor_decay([("a", 1.0, 100)], full_weight_seconds=100, zero_weight_seconds=100)


def test_apply_decay_dispatches_by_name():
    out = apply_decay("exponential", [("a", 1.0, 0.0)], half_life_seconds=3600)
    assert out == [("a", 1.0)]


def test_apply_decay_unknown_function_raises():
    with pytest.raises(ValueError):
        apply_decay("nope", [("a", 1.0, 0.0)])


def test_safe_age_seconds_rejects_negative():
    assert safe_age_seconds(100, 200) == 0.0


def test_safe_age_seconds_rejects_nan():
    assert safe_age_seconds(float("nan"), 0) == 0.0


def test_safe_age_seconds_rejects_inf():
    assert safe_age_seconds(float("inf"), 0) == 0.0


def test_safe_age_seconds_normal_case():
    assert safe_age_seconds(1000.0, 100.0) == 900.0


def test_decay_empty_input_returns_empty():
    assert exponential_decay([]) == []
    assert half_life_decay([]) == []
    assert linear_floor_decay([]) == []
