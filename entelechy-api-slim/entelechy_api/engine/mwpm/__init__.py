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

from pydantic import BaseModel, Field, model_validator


class PolicyParams(BaseModel):
    """Structured inference-time control state — the output of MWPM.

    Each field is a behavioral weighting parameter derived from memory
    frequency, recency, and semantic clustering. Applied at LLM call sites
    via the SVT-CP vFinal System Control Vector injection.
    """

    verbosity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Response verbosity scale [0, 1].",
    )
    abstraction: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Concept abstraction level [0, 1].",
    )
    creativity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Generative creativity vs determinism [0, 1].",
    )
    empathy: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Emotional engagement level [0, 1].",
    )
    rigor: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Logical strictness and step-by-step enforcement [0, 1].",
    )
    tool_use_probability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Probability of selecting an external tool over internal generation [0, 1].",
    )
    rationale: str = Field(
        default="",
        description="One-line explanation of why these params — audit + patent evidence.",
    )

    # Legacy fields (backwards compatibility)
    verbosity_target: int = Field(
        default=3,
        description="Old verbosity target [1, 5], mapped to verbosity.",
    )
    temperature_modifier: float = Field(
        default=0.0,
        description="Old temperature modifier, mapped to creativity.",
    )
    reasoning_depth: int = Field(
        default=3,
        description="Old reasoning depth [1, 5], mapped to rigor.",
    )
    tool_bias: dict[str, float] = Field(
        default_factory=dict,
        description="Old tool bias dict.",
    )
    uncertainty_threshold: float = Field(
        default=0.0,
        description="Old uncertainty threshold.",
    )

    @model_validator(mode="before")
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Map legacy fields to new float scalars if legacy fields are provided
        if "verbosity_target" in data and "verbosity" not in data:
            vt = data["verbosity_target"]
            data["verbosity"] = max(0.0, min(1.0, (vt - 1) / 4.0))

        if "temperature_modifier" in data and "creativity" not in data:
            tm = data["temperature_modifier"]
            data["creativity"] = max(0.0, min(1.0, tm + 0.5))

        if "reasoning_depth" in data and "rigor" not in data:
            rd = data["reasoning_depth"]
            data["rigor"] = max(0.0, min(1.0, (rd - 1) / 4.0))

        # Map new fields back to legacy fields if new ones are provided
        if "verbosity" in data and "verbosity_target" not in data:
            v = data["verbosity"]
            data["verbosity_target"] = int(round(v * 4 + 1))

        if "creativity" in data and "temperature_modifier" not in data:
            c = data["creativity"]
            data["temperature_modifier"] = c - 0.5

        if "rigor" in data and "reasoning_depth" not in data:
            r = data["rigor"]
            data["reasoning_depth"] = int(round(r * 4 + 1))

        return data

    @model_validator(mode="after")
    def post_validate(self) -> "PolicyParams":
        # Ensure consistency across both fields after construction/update
        self.verbosity_target = int(round(self.verbosity * 4 + 1))
        self.temperature_modifier = self.creativity - 0.5
        self.reasoning_depth = int(round(self.rigor * 4 + 1))
        return self

    class Config:
        from_attributes = True

    def merge(self, other: "PolicyParams") -> "PolicyParams":
        """Compose two PolicyParams. `other` wins on scalar overrides."""
        rationale = self.rationale
        if other.rationale:
            rationale = f"{rationale}; {other.rationale}" if rationale else other.rationale

        return PolicyParams(
            verbosity=other.verbosity,
            abstraction=other.abstraction,
            creativity=other.creativity,
            empathy=other.empathy,
            rigor=other.rigor,
            tool_use_probability=other.tool_use_probability,
            rationale=rationale,
            tool_bias=other.tool_bias if other.tool_bias else self.tool_bias,
            uncertainty_threshold=other.uncertainty_threshold
            if other.uncertainty_threshold != 0.0
            else self.uncertainty_threshold,
        )

    def to_system_control_vector(self) -> str:
        """Render the policy as the SVT-CP vFinal prompt injection block."""
        return (
            "SYSTEM CONTROL VECTOR:\n"
            f"- verbosity: {self.verbosity:.2f}\n"
            f"- abstraction: {self.abstraction:.2f}\n"
            f"- empathy: {self.empathy:.2f}\n"
            f"- rigor: {self.rigor:.2f}\n"
            f"- creativity: {self.creativity:.2f}\n"
            f"- tool_use: {self.tool_use_probability:.2f}"
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

    def lerp_float(a: float, b: float) -> float:
        return a + (b - a) * f

    return PolicyParams(
        verbosity=lerp_float(left.verbosity, right.verbosity),
        abstraction=lerp_float(left.abstraction, right.abstraction),
        creativity=lerp_float(left.creativity, right.creativity),
        empathy=lerp_float(left.empathy, right.empathy),
        rigor=lerp_float(left.rigor, right.rigor),
        tool_use_probability=lerp_float(left.tool_use_probability, right.tool_use_probability),
        rationale=left.rationale if f < 0.5 else right.rationale,
        tool_bias=left.tool_bias if f < 0.5 else right.tool_bias,
        uncertainty_threshold=lerp_float(left.uncertainty_threshold, right.uncertainty_threshold),
    )


@dataclass
class MemoryStats:
    """Statistics over a recall result — input to the MWPM modulator.

    Represents Vector F in the SVT-CP vFinal specification.
    """

    total_memories: int = 0
    tag_frequency: dict[str, int] = field(default_factory=dict)
    tag_recency_weighted: dict[str, float] = field(default_factory=dict)
    tag_clusters: list[list[str]] = field(default_factory=list)
    mean_age_seconds: float = 0.0
    fact_type_counts: dict[str, int] = field(default_factory=dict)
    signal_density: float = 0.0  # mean rerank score, 0..1

    # SVT-CP Vector F extensions
    avg_affect: float = 0.0
    success_rate: float = 0.0
    semantic_diversity: float = 0.0
    user_stability: float = 0.0

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
