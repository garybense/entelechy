"""Unit tests for entelechy_api.engine.mwpm.modulator.modulate_policy."""

from datetime import datetime, timezone

from entelechy_api.engine.mwpm import MemoryStats, PolicyParams
from entelechy_api.engine.mwpm.modulator import modulate_policy
from entelechy_api.engine.srl import StateVector


def _make_state_vector(**overrides) -> StateVector:
    defaults = {
        "posture_vector": {},
        "aesthetic_vector": {},
        "covenant_active": [],
        "active_focus": [],
        "drift_signal": 0.0,
        "affect_signature": {},
        "persona_lens": None,
        "transient_modifiers": {},
        "reconstruction_id": "test-recon",
        "reconstructed_at": datetime.now(timezone.utc),
        "source_memory_ids": [],
        "decay_profile": {},
    }
    defaults.update(overrides)
    return StateVector(**defaults)


def test_modulate_neutral_inputs_yields_baseline_with_rationale():
    sv = _make_state_vector()
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.reasoning_depth == 3
    assert p.verbosity_target == 3
    assert p.rationale == "neutral baseline"


def test_modulate_high_signal_density_increases_depth():
    sv = _make_state_vector()
    stats = MemoryStats(total_memories=10, signal_density=0.85)
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.reasoning_depth >= 4
    assert "signal_density" in p.rationale


def test_modulate_high_drift_increases_depth_and_uncertainty():
    sv = _make_state_vector(drift_signal=0.7)
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.reasoning_depth >= 4
    assert p.uncertainty_threshold > 0.5
    assert "drift" in p.rationale


def test_modulate_skeptical_posture_increases_depth():
    sv = _make_state_vector(posture_vector={"skeptical": 0.8, "precise": 0.6})
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.reasoning_depth >= 4


def test_modulate_intuitive_posture_decreases_depth():
    sv = _make_state_vector(posture_vector={"intuitive": 0.9, "rapid": 0.7})
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.reasoning_depth <= 2


def test_modulate_density_aesthetic_decreases_verbosity():
    sv = _make_state_vector(aesthetic_vector={"density": 0.9, "compressed": 0.7})
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.verbosity_target <= 2


def test_modulate_expansive_aesthetic_increases_verbosity():
    sv = _make_state_vector(aesthetic_vector={"verbose": 0.8, "narrative": 0.6})
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.verbosity_target >= 4


def test_modulate_verify_covenant_raises_uncertainty_floor():
    sv = _make_state_vector(covenant_active=["verify before claiming", "no half measures"])
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.uncertainty_threshold > 0.5
    assert "verification" in p.rationale or "verify" in p.rationale.lower()


def test_modulate_explore_covenant_lowers_uncertainty_floor():
    sv = _make_state_vector(covenant_active=["explore freely", "speculate often"])
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.uncertainty_threshold < 0.5


def test_modulate_top_tags_propagate_into_goal_priority_and_tool_bias():
    sv = _make_state_vector()
    stats = MemoryStats(
        total_memories=4,
        tag_recency_weighted={"metacog:felt-sense": 5.0, "metacog:naming": 3.0},
        tag_frequency={"metacog:felt-sense": 4, "metacog:naming": 3},
    )
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    # tags landed in goal_priority
    assert "metacog:felt-sense" in p.goal_priority
    # tag_to_tool_hint mapped tags onto tool names
    assert "feel" in p.tool_bias
    assert "name" in p.tool_bias
    assert p.tool_bias["feel"] > 1.0


def test_modulate_active_focus_lands_in_goal_priority():
    sv = _make_state_vector(active_focus=["build srl", "ship phase b"])
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert "build srl" in p.goal_priority
    assert "ship phase b" in p.goal_priority


def test_modulate_transient_modifiers_shift_temperature():
    sv = _make_state_vector(transient_modifiers={"caffeine": 0.6})
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.temperature_modifier > 0.0
    assert "transient" in p.rationale


def test_modulate_negative_transient_modifiers_lower_temperature():
    sv = _make_state_vector(transient_modifiers={"sedative": -0.8})
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.temperature_modifier < 0.0


def test_modulate_persona_lens_recorded_in_rationale():
    sv = _make_state_vector(persona_lens="research_mentor")
    stats = MemoryStats()
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert "research_mentor" in p.rationale


def test_modulate_respects_custom_baseline():
    sv = _make_state_vector()
    stats = MemoryStats()
    base = PolicyParams(reasoning_depth=4, tool_bias={"recall": 1.5})
    p = modulate_policy(state_vector=sv, memory_stats=stats, base=base)
    # baseline depth carries through
    assert p.reasoning_depth == 4
    # baseline tool bias preserved
    assert p.tool_bias["recall"] == 1.5
