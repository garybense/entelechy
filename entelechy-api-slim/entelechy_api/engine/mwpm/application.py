"""Apply PolicyParams to runtime call sites.

Pure functions that take PolicyParams plus base inputs and return modulated
outputs. No engine wiring here — the engine is wired to call these in a
later phase, gated by an opt-in flag so existing recall / reflect / distill
behavior is preserved by default.

Three application surfaces:
1. LLM call kwargs — scale max_completion_tokens, adjust temperature
2. Recall budget — scale strategy budget by reasoning_depth
3. Tool selection — filter / re-rank an available tool set by tool_bias
"""

from __future__ import annotations

from typing import Any

from . import PolicyParams

# Verbosity target → max_completion_tokens scale factor (1.0 = base default)
_VERBOSITY_TOKEN_SCALE = {
    1: 0.30,
    2: 0.60,
    3: 1.00,
    4: 1.50,
    5: 2.20,
}

# Reasoning depth → strategy budget scale factor
_DEPTH_BUDGET_SCALE = {
    1: 0.50,
    2: 0.75,
    3: 1.00,
    4: 1.40,
    5: 2.00,
}


def apply_to_llm_kwargs(
    params: PolicyParams,
    base_kwargs: dict[str, Any] | None = None,
    *,
    base_temperature: float = 0.7,
    base_max_tokens: int = 4096,
) -> dict[str, Any]:
    """Return an LLM-call kwarg dict with PolicyParams applied.

    `base_kwargs` is the caller's existing kwarg dict (may be None). Existing
    keys are preserved when the caller has explicitly set them; we only
    populate keys that are absent or marked for modulation.
    """
    out: dict[str, Any] = dict(base_kwargs or {})

    scale = _VERBOSITY_TOKEN_SCALE.get(params.verbosity_target, 1.0)
    target_max_tokens = max(64, int(base_max_tokens * scale))
    out.setdefault("max_completion_tokens", target_max_tokens)

    raw_temperature = base_temperature + params.temperature_modifier
    out.setdefault("temperature", _clamp(raw_temperature, 0.0, 2.0))

    return out


def scale_recall_budget(
    params: PolicyParams,
    base_budget: int,
) -> int:
    """Scale a recall strategy budget by reasoning_depth."""
    scale = _DEPTH_BUDGET_SCALE.get(params.reasoning_depth, 1.0)
    return max(1, int(base_budget * scale))


def select_tool_subset(
    params: PolicyParams,
    available_tools: list[str],
    *,
    cutoff: float = 0.5,
    max_tools: int | None = None,
) -> list[str]:
    """Filter / order available tools by PolicyParams.tool_bias.

    Tools without a bias entry get a baseline weight of 1.0. Tools below
    `cutoff` are dropped. Result is ordered by descending weight.
    """
    weighted: list[tuple[str, float]] = []
    for tool in available_tools:
        weight = params.tool_bias.get(tool, 1.0)
        if weight >= cutoff:
            weighted.append((tool, weight))

    weighted.sort(key=lambda t: t[1], reverse=True)
    selected = [tool for tool, _ in weighted]
    if max_tools is not None:
        selected = selected[:max_tools]
    return selected


def should_hedge(
    params: PolicyParams,
    confidence: float,
) -> bool:
    """True when caller should hedge / refuse — confidence below uncertainty floor."""
    return confidence < params.uncertainty_threshold


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
