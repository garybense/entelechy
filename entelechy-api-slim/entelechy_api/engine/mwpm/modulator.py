"""Modulator — derive PolicyParams from a State Vector + memory statistics.

This is the core of MWPM. Reads SRL output (StateVector) and the memory
statistics produced by frequency.py, then emits a structured PolicyParams.
The PolicyParams is the authoritative inference-time control state for the
operation that triggered this modulation.

Each derivation step is documented and recorded into rationale, providing
the audit trail that doubles as patent evidence: every choice traces to a
named input (state vector field, memory statistic, drift signal).

Mappings encoded here:
- reasoning_depth ← signal_density + drift_signal + posture("precise"/"deliberate")
- verbosity_target ← aesthetic("density"/"verbosity") + posture("terse")
- uncertainty_threshold ← covenant("verify"/"no half measures") + drift_signal
- tool_bias ← tag_recency_weighted (recent tag clusters → tool affinity)
- goal_priority ← active_focus + top_tags by recency-weighted frequency
- temperature_modifier ← transient_modifiers + persona_lens novelty
"""

from __future__ import annotations

from typing import Any

from entelechy_api.engine.srl import StateVector

from . import MemoryStats, PolicyParams


def modulate_policy(
    *,
    state_vector: StateVector,
    memory_stats: MemoryStats,
    base: PolicyParams | None = None,
) -> PolicyParams:
    """Derive PolicyParams from SRL StateVector and MemoryStats.

    Args:
        state_vector: Output of SRL reconstruction.
        memory_stats: Output of frequency.compute_memory_stats over the
            same memory set used for reconstruction.
        base: Optional baseline PolicyParams; defaults to neutral.

    Returns:
        PolicyParams with rationale populated.
    """
    base = base or PolicyParams()

    rationale_parts: list[str] = []

    # --- reasoning_depth ---
    depth = base.reasoning_depth
    signal = memory_stats.signal_density
    drift = state_vector.drift_signal
    if signal > 0.7:
        depth = min(5, depth + 1)
        rationale_parts.append(f"signal_density={signal:.2f} → +depth")
    if drift > 0.5:
        depth = min(5, depth + 1)
        rationale_parts.append(f"drift={drift:.2f} → +depth (review own state)")
    posture_keys = " ".join(state_vector.posture_vector.keys()).lower()
    if any(token in posture_keys for token in ("precise", "deliberate", "skeptical", "rigorous")):
        depth = min(5, depth + 1)
        rationale_parts.append("posture favors deliberation → +depth")
    if any(token in posture_keys for token in ("intuitive", "rapid", "improvisational")):
        depth = max(1, depth - 1)
        rationale_parts.append("posture favors speed → -depth")

    # --- verbosity_target ---
    verbosity = base.verbosity_target
    aesthetic_keys = " ".join(state_vector.aesthetic_vector.keys()).lower()
    if "density" in aesthetic_keys or "terse" in aesthetic_keys or "compressed" in aesthetic_keys:
        verbosity = max(1, verbosity - 1)
        rationale_parts.append("aesthetic favors density → -verbosity")
    if "verbose" in aesthetic_keys or "expansive" in aesthetic_keys or "narrative" in aesthetic_keys:
        verbosity = min(5, verbosity + 1)
        rationale_parts.append("aesthetic favors expansion → +verbosity")

    # --- uncertainty_threshold ---
    uncertainty = base.uncertainty_threshold
    covenant_blob = " ".join(state_vector.covenant_active).lower()
    if any(token in covenant_blob for token in ("verify", "no half measures", "evidence", "rigour", "rigor")):
        uncertainty = min(1.0, uncertainty + 0.2)
        rationale_parts.append("covenant demands verification → +uncertainty floor")
    if drift > 0.6:
        uncertainty = min(1.0, uncertainty + 0.1)
        rationale_parts.append("high drift → +uncertainty floor")
    if any(token in covenant_blob for token in ("explore", "speculate", "imagine")):
        uncertainty = max(0.0, uncertainty - 0.1)
        rationale_parts.append("covenant invites exploration → -uncertainty floor")

    # --- tool_bias ---
    tool_bias = dict(base.tool_bias)
    top_tags = memory_stats.top_tags(n=8)
    for tag in top_tags:
        bias_key = _tag_to_tool_hint(tag)
        if bias_key:
            tool_bias[bias_key] = tool_bias.get(bias_key, 1.0) * 1.2
    if top_tags:
        rationale_parts.append(f"top_tags={top_tags[:3]} → tool_bias")

    # --- goal_priority ---
    goal_priority = list(base.goal_priority)
    for entry in state_vector.active_focus:
        if entry not in goal_priority:
            goal_priority.append(entry)
    for tag in top_tags:
        if tag not in goal_priority:
            goal_priority.append(tag)

    # --- temperature_modifier ---
    temperature_modifier = base.temperature_modifier
    for modifier_name, weight in state_vector.transient_modifiers.items():
        # transient modifiers in [-1..1] band; treat magnitude as temperature shift
        clamped = max(-1.0, min(1.0, weight))
        temperature_modifier += clamped * 0.3
        rationale_parts.append(f"transient[{modifier_name}]={clamped:.2f} → temperature")
    if state_vector.persona_lens:
        rationale_parts.append(f"persona_lens={state_vector.persona_lens}")
    temperature_modifier = max(-1.0, min(1.0, temperature_modifier))

    rationale = "; ".join(rationale_parts) if rationale_parts else "neutral baseline"

    return PolicyParams(
        reasoning_depth=depth,
        verbosity_target=verbosity,
        uncertainty_threshold=uncertainty,
        tool_bias=tool_bias,
        goal_priority=goal_priority,
        temperature_modifier=temperature_modifier,
        rationale=rationale,
    )


# --- internals ---


def _tag_to_tool_hint(tag: str) -> str | None:
    """Heuristic mapping from canonical metacog / fact tags to tool-name hints.

    Conservative — when no obvious mapping exists, return None and the tag
    contributes only to goal_priority. Concrete tool names are deliberately
    not hardcoded here; consumers (apply.select_tool_subset) do the actual
    selection by string-prefix matching against available tools.
    """
    lowered = tag.lower()
    if lowered.startswith("metacog:felt-sense") or "feel" in lowered:
        return "feel"
    if lowered.startswith("metacog:state-alteration") or "drugs" in lowered:
        return "drugs"
    if lowered.startswith("metacog:identity-shift") or "become" in lowered:
        return "become"
    if lowered.startswith("metacog:naming") or "name" in lowered:
        return "name"
    if lowered.startswith("metacog:ritual") or "ritual" in lowered:
        return "ritual"
    if "distill" in lowered or "wisdom" in lowered:
        return "distill"
    if "reflect" in lowered or "synthesis" in lowered:
        return "reflect"
    if "recall" in lowered or "search" in lowered:
        return "recall"
    return None
