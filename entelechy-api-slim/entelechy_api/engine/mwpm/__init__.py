"""Memory-Weighted Policy Modulation (MWPM) — Primitive 2 of the closed-loop
state-conditioned generative control system.

MWPM consumes the State Vector produced by SRL plus memory-frequency / recency /
semantic-cluster statistics, then emits a structured PolicyParams object that
modulates inference-time controls: reasoning depth, verbosity, uncertainty
calibration, tool selection bias, goal prioritization, and temperature.

This is active inference policy alteration. Memory is not retrieved-and-injected;
memory is the *substrate* whose statistical structure conditions runtime behavior.
The synergy of SRL + MWPM is the patentable competitive advantage.

Time-variant policies: PolicyParams may be wrapped in a TimeVariantPolicy that
returns concrete params as a function of time-since-onset. This supports the
canonical drugs() primitive — the cognitive-substrate alteration that demands
onset / peak / comedown curves rather than static deltas. The temporal-curve
formulation of policy modulation, keyed off classified-substrate models, is an
unobvious extension of MWPM that strengthens Claim 2.

Module layout:
- PolicyParams: structured inference-time control state
- TimeVariantPolicy: anchor-interpolated curve over PolicyParams
- frequency: memory frequency / recency / cluster statistics
- modulator: derive PolicyParams from StateVector + MemoryStats
- application: apply PolicyParams to LLM kwargs / recall budget / tool selection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class PolicyParams(BaseModel):
    """Structured inference-time control state — the output of MWPM.

    Each field is a behavioral weighting parameter derived from memory
    frequency, recency, and semantic clustering. Applied at LLM call sites,
    retrieval budget allocation, and tool selection.
    """

    reasoning_depth: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Chain-of-thought depth budget. 1 = terse direct answer, 5 = full deliberation.",
    )
    verbosity_target: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Response token target band. 1 = minimal, 5 = expansive.",
    )
    uncertainty_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence floor below which the model should hedge or refuse.",
    )
    tool_bias: dict[str, float] = Field(
        default_factory=dict,
        description="Multiplier per tool name applied to selection score. >1 favors, <1 disfavors.",
    )
    goal_priority: list[str] = Field(
        default_factory=list,
        description="Ordered tag list. Earlier entries take precedence in goal conflicts.",
    )
    temperature_modifier: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Delta applied to base sampling temperature.",
    )
    rationale: str = Field(
        default="",
        description="One-line explanation of why these params — audit + patent evidence.",
    )

    class Config:
        from_attributes = True

    def merge(self, other: "PolicyParams") -> "PolicyParams":
        """Compose two PolicyParams. `other` wins on scalar overrides; dict and
        list fields are merged additively / by union."""
        merged_tool_bias = dict(self.tool_bias)
        for tool, weight in other.tool_bias.items():
            merged_tool_bias[tool] = merged_tool_bias.get(tool, 1.0) * weight

        # goal_priority: append unique entries from other in order, preserving precedence
        merged_priority = list(self.goal_priority)
        for tag in other.goal_priority:
            if tag not in merged_priority:
                merged_priority.append(tag)

        rationale = self.rationale
        if other.rationale:
            rationale = f"{rationale}; {other.rationale}" if rationale else other.rationale

        return PolicyParams(
            reasoning_depth=other.reasoning_depth,
            verbosity_target=other.verbosity_target,
            uncertainty_threshold=other.uncertainty_threshold,
            tool_bias=merged_tool_bias,
            goal_priority=merged_priority,
            temperature_modifier=self.temperature_modifier + other.temperature_modifier,
            rationale=rationale,
        )

    def with_rationale(self, rationale: str) -> "PolicyParams":
        """Return a copy with the rationale field replaced."""
        return self.model_copy(update={"rationale": rationale})


@dataclass(frozen=True)
class CurveAnchor:
    """A (t, params) anchor point on a TimeVariantPolicy curve."""

    t_seconds: float
    params: PolicyParams


@dataclass
class TimeVariantPolicy:
    """A piecewise-linear interpolation over PolicyParams anchors.

    Used by drugs() and other transient-modulation primitives to express
    onset → peak → comedown curves. evaluate_at(t) returns concrete
    PolicyParams that callers apply at runtime.

    Anchors must be supplied in non-decreasing order of t_seconds. For t
    before the first anchor, the first anchor is returned. For t after the
    last anchor, the last anchor is returned (no extrapolation).
    """

    baseline: PolicyParams
    anchors: list[CurveAnchor] = field(default_factory=list)
    label: str = ""

    def evaluate_at(self, t_seconds: float) -> PolicyParams:
        """Return concrete PolicyParams for the given time offset."""
        if not self.anchors:
            return self.baseline

        if t_seconds <= self.anchors[0].t_seconds:
            return self.baseline.merge(self.anchors[0].params)

        if t_seconds >= self.anchors[-1].t_seconds:
            return self.baseline.merge(self.anchors[-1].params)

        # Find the segment containing t
        for i in range(len(self.anchors) - 1):
            left = self.anchors[i]
            right = self.anchors[i + 1]
            if left.t_seconds <= t_seconds <= right.t_seconds:
                span = right.t_seconds - left.t_seconds
                if span <= 0:
                    return self.baseline.merge(left.params)
                fraction = (t_seconds - left.t_seconds) / span
                interpolated = _interpolate_params(left.params, right.params, fraction)
                return self.baseline.merge(interpolated)

        # Should be unreachable — defensive return
        return self.baseline.merge(self.anchors[-1].params)


def _interpolate_params(left: PolicyParams, right: PolicyParams, fraction: float) -> PolicyParams:
    """Linear interpolation between two PolicyParams at `fraction` ∈ [0, 1]."""
    f = max(0.0, min(1.0, fraction))

    def lerp_int(a: int, b: int) -> int:
        return int(round(a + (b - a) * f))

    def lerp_float(a: float, b: float) -> float:
        return a + (b - a) * f

    # Tool bias: keys union; weights linearly interpolated, missing keys assumed 1.0
    keys = set(left.tool_bias) | set(right.tool_bias)
    tool_bias = {k: lerp_float(left.tool_bias.get(k, 1.0), right.tool_bias.get(k, 1.0)) for k in keys}

    # Goal priority: blend by taking left near f=0 and right near f=1
    if f < 0.5:
        goal_priority = list(left.goal_priority)
        for tag in right.goal_priority:
            if tag not in goal_priority:
                goal_priority.append(tag)
    else:
        goal_priority = list(right.goal_priority)
        for tag in left.goal_priority:
            if tag not in goal_priority:
                goal_priority.append(tag)

    return PolicyParams(
        reasoning_depth=lerp_int(left.reasoning_depth, right.reasoning_depth),
        verbosity_target=lerp_int(left.verbosity_target, right.verbosity_target),
        uncertainty_threshold=lerp_float(left.uncertainty_threshold, right.uncertainty_threshold),
        tool_bias=tool_bias,
        goal_priority=goal_priority,
        temperature_modifier=lerp_float(left.temperature_modifier, right.temperature_modifier),
        rationale=left.rationale if f < 0.5 else right.rationale,
    )


@dataclass
class MemoryStats:
    """Statistics over a recall result — input to the MWPM modulator.

    All fields are derived from recall outputs; no separate query is required.
    """

    total_memories: int = 0
    tag_frequency: dict[str, int] = field(default_factory=dict)
    tag_recency_weighted: dict[str, float] = field(default_factory=dict)
    tag_clusters: list[list[str]] = field(default_factory=list)
    mean_age_seconds: float = 0.0
    fact_type_counts: dict[str, int] = field(default_factory=dict)
    signal_density: float = 0.0  # mean rerank score, 0..1

    def top_tags(self, n: int = 5) -> list[str]:
        """Return the top-N tags by recency-weighted frequency."""
        ranked = sorted(self.tag_recency_weighted.items(), key=lambda t: t[1], reverse=True)
        return [tag for tag, _ in ranked[:n]]


__all__ = [
    "CurveAnchor",
    "MemoryStats",
    "PolicyParams",
    "TimeVariantPolicy",
]


# Sentinel used by callers that explicitly want "no modulation". Distinct from
# omitting PolicyParams entirely (which means "use defaults from base config").
def neutral() -> PolicyParams:
    return PolicyParams(rationale="neutral baseline")
