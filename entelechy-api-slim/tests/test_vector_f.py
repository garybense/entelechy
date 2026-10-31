import math
import time
from types import SimpleNamespace

from entelechy_api.engine.mwpm.frequency import derive_vector_f
from entelechy_api.engine.mwpm.modulator import modulate_policy


def mem(i, tags):
    return {"id": str(i), "text": f"m{i}", "tags": tags, "score": 0.9, "fact_type": "experience"}


def test_empty_bank_is_neutral():
    s = derive_vector_f([], now_epoch=time.time())
    assert s.total_memories == 0
    assert s.success_rate == 0.5 and s.semantic_diversity == 0.0 and s.avg_affect == 0.0


def test_diversity_is_entropy_of_tags():
    even = derive_vector_f([mem(1, ["a"]), mem(2, ["b"]), mem(3, ["c"])], now_epoch=time.time())
    skew = derive_vector_f([mem(i, ["a"]) for i in range(9)] + [mem(9, ["b"])], now_epoch=time.time())
    assert math.isclose(even.semantic_diversity, 1.0)
    assert 0 < skew.semantic_diversity < 0.6


def test_success_rate_from_outcome_tags():
    ms = [mem(1, ["outcome:success"]), mem(2, ["outcome:success"]), mem(3, ["outcome:failure"])]
    s = derive_vector_f(ms, now_epoch=time.time())
    assert math.isclose(s.success_rate, 2 / 3)


def test_state_vector_drives_affect_and_stability():
    sv = SimpleNamespace(affect_signature={"warmth": 0.8, "tension": 0.4}, drift_signal=0.25)
    with_cp = derive_vector_f([mem(1, ["a"])], now_epoch=time.time(), state_vector=sv, has_checkpoint=True)
    no_cp = derive_vector_f([mem(1, ["a"])], now_epoch=time.time(), state_vector=sv)
    assert math.isclose(with_cp.avg_affect, 0.6) and math.isclose(with_cp.user_stability, 0.75)
    assert no_cp.user_stability == 0.0


def test_modulator_moves_with_real_stats():
    ms = [mem(1, ["outcome:failure"]), mem(2, ["x"]), mem(3, ["y"])]
    low = modulate_policy(state_vector=None, memory_stats=derive_vector_f(ms, now_epoch=time.time()))
    neutral = modulate_policy(state_vector=None, memory_stats=derive_vector_f([], now_epoch=time.time()))
    assert low.creativity > neutral.creativity
