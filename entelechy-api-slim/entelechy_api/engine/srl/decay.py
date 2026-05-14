"""Temporal decay functions for the weighted episodic memory graph.

Decay is applied to memory retrieval scores prior to retrieval-conditioned
synthesis. The decay profile chosen for a given reconstruction is recorded
on the resulting StateVector for audit and patent evidence.

All decay functions take a list of (memory_id, base_score, age_seconds) triples
and return a list of (memory_id, weighted_score) pairs sorted by weighted_score.
Pure functions — no I/O, no side effects.
"""

import math
from collections.abc import Iterable

DecayInput = tuple[str, float, float]
DecayOutput = tuple[str, float]


def exponential_decay(
    items: Iterable[DecayInput],
    *,
    half_life_seconds: float = 86400.0,
) -> list[DecayOutput]:
    """Multiplicative exponential decay weighted by half-life.

    weighted = base_score * 2 ** (-age / half_life)

    Use when recency dominates relevance — recent felt-sense, recent drugs(),
    recent become() should outweigh older entries by a large factor.
    """
    if half_life_seconds <= 0:
        raise ValueError("half_life_seconds must be > 0")
    out: list[DecayOutput] = []
    for memory_id, base_score, age_seconds in items:
        weight = 2.0 ** (-max(age_seconds, 0.0) / half_life_seconds)
        out.append((memory_id, base_score * weight))
    out.sort(key=lambda t: t[1], reverse=True)
    return out


def half_life_decay(
    items: Iterable[DecayInput],
    *,
    half_life_seconds: float = 86400.0,
    floor: float = 0.05,
) -> list[DecayOutput]:
    """Exponential decay with a non-zero floor.

    Identical to exponential_decay but clamps the multiplier to `floor` so
    very old memories retain a baseline contribution. Use when long-arc
    pattern recall matters even for ancient entries (covenant lineage,
    ritual ancestry).
    """
    if half_life_seconds <= 0:
        raise ValueError("half_life_seconds must be > 0")
    if not (0.0 <= floor <= 1.0):
        raise ValueError("floor must be in [0, 1]")
    out: list[DecayOutput] = []
    for memory_id, base_score, age_seconds in items:
        raw = 2.0 ** (-max(age_seconds, 0.0) / half_life_seconds)
        weight = max(raw, floor)
        out.append((memory_id, base_score * weight))
    out.sort(key=lambda t: t[1], reverse=True)
    return out


def linear_floor_decay(
    items: Iterable[DecayInput],
    *,
    full_weight_seconds: float = 3600.0,
    zero_weight_seconds: float = 2_592_000.0,
    floor: float = 0.1,
) -> list[DecayOutput]:
    """Piecewise linear decay with a non-zero floor.

    weight = 1.0                                          for age <= full_weight_seconds
    weight = lerp(1.0, floor, fraction_in_decay_band)     for age in (full, zero)
    weight = floor                                        for age >= zero_weight_seconds

    Use when the curve should be predictable — useful for compass drift
    detection where reviewers must read the score back to a memory's age.
    """
    if full_weight_seconds < 0 or zero_weight_seconds <= full_weight_seconds:
        raise ValueError("require 0 <= full_weight_seconds < zero_weight_seconds")
    if not (0.0 <= floor <= 1.0):
        raise ValueError("floor must be in [0, 1]")
    span = zero_weight_seconds - full_weight_seconds
    out: list[DecayOutput] = []
    for memory_id, base_score, age_seconds in items:
        age = max(age_seconds, 0.0)
        if age <= full_weight_seconds:
            weight = 1.0
        elif age >= zero_weight_seconds:
            weight = floor
        else:
            fraction = (age - full_weight_seconds) / span
            weight = 1.0 - fraction * (1.0 - floor)
        out.append((memory_id, base_score * weight))
    out.sort(key=lambda t: t[1], reverse=True)
    return out


# Registry — name → callable, exposed for serialization on StateVector.decay_profile.
DECAY_FUNCTIONS = {
    "exponential": exponential_decay,
    "half_life": half_life_decay,
    "linear_floor": linear_floor_decay,
}


def apply_decay(
    name: str,
    items: Iterable[DecayInput],
    **params: float,
) -> list[DecayOutput]:
    """Dispatch to a registered decay function by name."""
    fn = DECAY_FUNCTIONS.get(name)
    if fn is None:
        raise ValueError(f"unknown decay function: {name!r}")
    return fn(items, **params)


def safe_age_seconds(now_epoch: float, then_epoch: float) -> float:
    """Compute non-negative age in seconds. NaN/inf-safe."""
    age = now_epoch - then_epoch
    if math.isnan(age) or math.isinf(age) or age < 0:
        return 0.0
    return age
