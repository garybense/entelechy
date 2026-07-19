"""Unit tests for entelechy_api.engine.mwpm.modulator.modulate_policy."""

import math
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
    assert p.verbosity == 0.5
    assert p.abstraction == 0.5
    assert p.creativity == 0.5
    assert p.empathy == 0.5
    assert p.rigor == 0.5
    assert p.tool_use_probability == 0.5
    assert "Neutral mathematical baseline" in p.rationale


def test_modulate_positive_affect_increases_empathy_and_verbosity():
    sv = _make_state_vector()
    stats = MemoryStats(avg_affect=0.8)
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.empathy > 0.5
    assert p.verbosity > 0.5
    assert p.rigor == 0.5
    assert "avg_affect" in p.rationale


def test_modulate_negative_affect_increases_rigor():
    sv = _make_state_vector()
    stats = MemoryStats(avg_affect=-0.6)
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.empathy == 0.5
    assert p.verbosity == 0.5
    assert p.rigor > 0.5
    assert "avg_affect" in p.rationale


def test_modulate_low_success_rate_increases_creativity_and_tool_use():
    sv = _make_state_vector()
    stats = MemoryStats(total_memories=10, success_rate=0.2)
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.creativity > 0.5
    assert p.tool_use_probability > 0.5
    assert "success_rate" in p.rationale


def test_modulate_high_semantic_diversity_increases_abstraction():
    sv = _make_state_vector()
    stats = MemoryStats(semantic_diversity=0.8)
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.abstraction > 0.5
    assert "semantic_diversity" in p.rationale


def test_modulate_high_user_stability_increases_rigor_decreases_creativity():
    sv = _make_state_vector()
    stats = MemoryStats(user_stability=0.9)
    p = modulate_policy(state_vector=sv, memory_stats=stats)
    assert p.rigor > 0.5
    assert p.creativity < 0.5
    assert "user_stability" in p.rationale


def test_policy_inertia_clamps_extreme_changes():
    sv = _make_state_vector()
    stats = MemoryStats(avg_affect=1.0) # Should try to push empathy to 0.5 + 0.2 = 0.7
    
    previous = PolicyParams(empathy=0.2) # Inertia delta is 0.5. Limit is 0.15
    p = modulate_policy(state_vector=sv, memory_stats=stats, previous_policy=previous, inertia_epsilon=0.15)
    
    # 0.2 + 0.15 limit = 0.35
    assert math.isclose(p.empathy, 0.35, abs_tol=1e-6)
    assert "inertia" in p.rationale.lower()


def test_modulate_respects_custom_baseline():
    sv = _make_state_vector()
    stats = MemoryStats()
    base = PolicyParams(rigor=0.8)
    p = modulate_policy(state_vector=sv, memory_stats=stats, base=base)
    # baseline depth carries through
    assert p.rigor == 0.8
    assert p.verbosity == 0.5