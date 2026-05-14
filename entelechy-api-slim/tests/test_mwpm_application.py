"""Unit tests for entelechy_api.engine.mwpm.application."""

from entelechy_api.engine.mwpm import PolicyParams
from entelechy_api.engine.mwpm.application import (
    apply_to_llm_kwargs,
    scale_recall_budget,
    select_tool_subset,
    should_hedge,
)


def test_apply_to_llm_kwargs_default_uses_base_max_tokens():
    p = PolicyParams()
    out = apply_to_llm_kwargs(p, base_max_tokens=4096, base_temperature=0.7)
    assert out["max_completion_tokens"] == 4096
    assert out["temperature"] == 0.7


def test_apply_to_llm_kwargs_high_verbosity_scales_tokens_up():
    p = PolicyParams(verbosity_target=5)
    out = apply_to_llm_kwargs(p, base_max_tokens=1000)
    assert out["max_completion_tokens"] > 1000


def test_apply_to_llm_kwargs_low_verbosity_scales_tokens_down():
    p = PolicyParams(verbosity_target=1)
    out = apply_to_llm_kwargs(p, base_max_tokens=1000)
    assert out["max_completion_tokens"] < 1000


def test_apply_to_llm_kwargs_temperature_modifier_applied():
    p = PolicyParams(temperature_modifier=0.3)
    out = apply_to_llm_kwargs(p, base_max_tokens=1000, base_temperature=0.5)
    assert abs(out["temperature"] - 0.8) < 1e-9


def test_apply_to_llm_kwargs_clamps_temperature_to_valid_band():
    p = PolicyParams(temperature_modifier=1.0)
    out = apply_to_llm_kwargs(p, base_temperature=1.8)
    assert out["temperature"] <= 2.0


def test_apply_to_llm_kwargs_preserves_existing_caller_kwargs():
    p = PolicyParams(verbosity_target=5)
    base_kwargs = {"max_completion_tokens": 100, "stop": ["\\n"]}
    out = apply_to_llm_kwargs(p, base_kwargs, base_max_tokens=4096)
    # caller's explicit override wins
    assert out["max_completion_tokens"] == 100
    assert out["stop"] == ["\\n"]


def test_scale_recall_budget_at_default_depth():
    assert scale_recall_budget(PolicyParams(reasoning_depth=3), 100) == 100


def test_scale_recall_budget_at_max_depth_doubles():
    assert scale_recall_budget(PolicyParams(reasoning_depth=5), 100) == 200


def test_scale_recall_budget_at_min_depth_halves():
    assert scale_recall_budget(PolicyParams(reasoning_depth=1), 100) == 50


def test_scale_recall_budget_floor_at_one():
    assert scale_recall_budget(PolicyParams(reasoning_depth=1), 1) >= 1


def test_select_tool_subset_orders_by_bias():
    p = PolicyParams(tool_bias={"distill": 2.0, "recall": 1.5, "reflect": 1.0})
    out = select_tool_subset(p, ["recall", "reflect", "distill", "feel"])
    # feel has no bias entry → defaults to 1.0; ordering by weight
    assert out[0] == "distill"
    assert out[1] == "recall"


def test_select_tool_subset_drops_below_cutoff():
    p = PolicyParams(tool_bias={"recall": 0.2, "distill": 1.5})
    out = select_tool_subset(p, ["recall", "distill"], cutoff=0.5)
    assert "recall" not in out
    assert "distill" in out


def test_select_tool_subset_respects_max_tools():
    p = PolicyParams(tool_bias={"a": 3.0, "b": 2.0, "c": 1.5})
    out = select_tool_subset(p, ["a", "b", "c"], max_tools=2)
    assert len(out) == 2
    assert out == ["a", "b"]


def test_select_tool_subset_default_weight_keeps_unmapped():
    p = PolicyParams(tool_bias={})
    out = select_tool_subset(p, ["recall", "reflect"])
    # No biases set; both default 1.0; both pass cutoff 0.5
    assert sorted(out) == ["recall", "reflect"]


def test_should_hedge_below_threshold_returns_true():
    p = PolicyParams(uncertainty_threshold=0.7)
    assert should_hedge(p, 0.5) is True


def test_should_hedge_above_threshold_returns_false():
    p = PolicyParams(uncertainty_threshold=0.7)
    assert should_hedge(p, 0.8) is False


def test_should_hedge_at_threshold_returns_false():
    # Strict less-than: confidence equal to threshold passes
    p = PolicyParams(uncertainty_threshold=0.7)
    assert should_hedge(p, 0.7) is False
