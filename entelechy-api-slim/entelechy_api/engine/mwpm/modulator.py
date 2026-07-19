"""Modulator — derive PolicyParams from a State Vector + memory statistics.

This implements the SVT-CP vFinal Policy Synthesis (Stage B).
Translates Vector F (MemoryStats) into Vector P (PolicyParams).
Enforces Policy Inertia to prevent catastrophic personality drift.
"""

from __future__ import annotations

import math
from typing import Any

from entelechy_api.engine.srl import StateVector

from . import MemoryStats, PolicyParams


def modulate_policy(
    *,
    state_vector: StateVector,
    memory_stats: MemoryStats,
    base: PolicyParams | None = None,
    previous_policy: PolicyParams | None = None,
    inertia_epsilon: float = 0.15,
) -> PolicyParams:
    """Derive PolicyParams from SRL StateVector and MemoryStats.

    Implements the core translation of Vector F -> Vector P.

    Args:
        state_vector: Output of SRL reconstruction.
        memory_stats: Vector F (extracted metrics from memory graph).
        base: Optional baseline PolicyParams; defaults to neutral 0.5 scalars.
        previous_policy: P_{t-1} for enforcing policy inertia.
        inertia_epsilon: Maximum allowed drift per modulation cycle.

    Returns:
        PolicyParams mapped to [0,1] bounds with rationale populated.
    """
    base = base or PolicyParams()

    rationale_parts: list[str] = []

    # Local mutable state for Vector P
    verbosity = base.verbosity
    abstraction = base.abstraction
    creativity = base.creativity
    empathy = base.empathy
    rigor = base.rigor
    tool_use = base.tool_use_probability

    # --- Feature Extraction (Vector F) translation ---

    # 1. Affect Modulation
    if memory_stats.avg_affect > 0:
        # Positive affect expands empathy and verbosity
        k1, k2 = 0.2, 0.1
        empathy += k1 * memory_stats.avg_affect
        verbosity += k2 * memory_stats.avg_affect
        rationale_parts.append(f"avg_affect={memory_stats.avg_affect:.2f} -> +empathy, +verbosity")
    elif memory_stats.avg_affect < 0:
        # Negative affect contracts into rigor
        k3 = 0.25
        rigor += k3 * abs(memory_stats.avg_affect)
        rationale_parts.append(f"avg_affect={memory_stats.avg_affect:.2f} -> +rigor")

    # 2. Task History Modulation
    if memory_stats.success_rate < 0.5 and memory_stats.total_memories > 0:
        # Failure loops demand greater creativity (variance) and tool reliance
        k4, k5 = 0.3, 0.2
        creativity += k4 * (0.5 - memory_stats.success_rate)
        tool_use += k5 * (0.5 - memory_stats.success_rate)
        rationale_parts.append(f"success_rate={memory_stats.success_rate:.2f} -> +creativity, +tool_use")

    # 3. Abstraction Drift
    k6 = 0.4
    if memory_stats.semantic_diversity > 0:
        abstraction += k6 * memory_stats.semantic_diversity
        rationale_parts.append(f"semantic_diversity={memory_stats.semantic_diversity:.2f} -> +abstraction")

    # 4. User Stability vs Generative Determinism
    if memory_stats.user_stability > 0.8:
        # Highly stable user intent allows for tighter, more deterministic rigorous responses
        rigor += 0.1
        creativity -= 0.1
        rationale_parts.append(f"user_stability={memory_stats.user_stability:.2f} -> +rigor, -creativity")

    # Clip constraints to [0, 1] bounds
    def clip(val: float) -> float:
        return max(0.0, min(1.0, val))

    proposed_verbosity = clip(verbosity)
    proposed_abstraction = clip(abstraction)
    proposed_creativity = clip(creativity)
    proposed_empathy = clip(empathy)
    proposed_rigor = clip(rigor)
    proposed_tool_use = clip(tool_use)

    # 5. Anti-Collapse Mechanism: Policy Inertia
    # ||P_t - P_t-1|| < epsilon
    if previous_policy is not None:

        def clamp_inertia(new_val: float, old_val: float) -> float:
            delta = new_val - old_val
            if abs(delta) > inertia_epsilon:
                return old_val + math.copysign(inertia_epsilon, delta)
            return new_val

        final_verbosity = clamp_inertia(proposed_verbosity, previous_policy.verbosity)
        final_abstraction = clamp_inertia(proposed_abstraction, previous_policy.abstraction)
        final_creativity = clamp_inertia(proposed_creativity, previous_policy.creativity)
        final_empathy = clamp_inertia(proposed_empathy, previous_policy.empathy)
        final_rigor = clamp_inertia(proposed_rigor, previous_policy.rigor)
        final_tool_use = clamp_inertia(proposed_tool_use, previous_policy.tool_use_probability)

        # Check if inertia was actually triggered to append rationale
        if (
            final_verbosity != proposed_verbosity
            or final_abstraction != proposed_abstraction
            or final_creativity != proposed_creativity
            or final_empathy != proposed_empathy
            or final_rigor != proposed_rigor
            or final_tool_use != proposed_tool_use
        ):
            rationale_parts.append("Policy inertia epsilon-bound enforced")
    else:
        final_verbosity = proposed_verbosity
        final_abstraction = proposed_abstraction
        final_creativity = proposed_creativity
        final_empathy = proposed_empathy
        final_rigor = proposed_rigor
        final_tool_use = proposed_tool_use

    rationale = "; ".join(rationale_parts) if rationale_parts else "Neutral mathematical baseline"

    return PolicyParams(
        verbosity=final_verbosity,
        abstraction=final_abstraction,
        creativity=final_creativity,
        empathy=final_empathy,
        rigor=final_rigor,
        tool_use_probability=final_tool_use,
        rationale=rationale,
    )
