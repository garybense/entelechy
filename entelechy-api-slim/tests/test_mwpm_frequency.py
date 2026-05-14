"""Unit tests for entelechy_api.engine.mwpm.frequency.compute_memory_stats."""

from datetime import datetime, timedelta, timezone

import pytest

from entelechy_api.engine.mwpm import MemoryStats
from entelechy_api.engine.mwpm.frequency import (
    _connected_components,
    _normalize_tags,
    _recency_weight,
    compute_memory_stats,
)


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def test_compute_memory_stats_empty_returns_default():
    stats = compute_memory_stats([], now_epoch=_now())
    assert isinstance(stats, MemoryStats)
    assert stats.total_memories == 0
    assert stats.tag_frequency == {}
    assert stats.signal_density == 0.0


def test_compute_memory_stats_counts_tags():
    now = _now()
    memories = [
        {"id": "1", "tags": ["a", "b"], "score": 0.8, "fact_type": "experience"},
        {"id": "2", "tags": ["b", "c"], "score": 0.6, "fact_type": "experience"},
        {"id": "3", "tags": ["b"], "score": 0.5, "fact_type": "world"},
    ]
    stats = compute_memory_stats(memories, now_epoch=now)
    assert stats.total_memories == 3
    assert stats.tag_frequency == {"a": 1, "b": 3, "c": 1}
    assert stats.fact_type_counts == {"experience": 2, "world": 1}


def test_compute_memory_stats_signal_density():
    memories = [
        {"id": "1", "tags": [], "score": 0.9},
        {"id": "2", "tags": [], "score": 0.5},
        {"id": "3", "tags": [], "score": 0.7},
    ]
    stats = compute_memory_stats(memories, now_epoch=_now())
    assert 0.65 < stats.signal_density < 0.75


def test_compute_memory_stats_recency_weighting_favors_recent():
    now = _now()
    recent_iso = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    old_iso = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    memories = [
        {"id": "1", "tags": ["fresh"], "score": 0.5, "event_date": recent_iso},
        {"id": "2", "tags": ["stale"], "score": 0.5, "event_date": old_iso},
    ]
    stats = compute_memory_stats(memories, now_epoch=now, recency_half_life_seconds=3600)
    # Both tags appear once, but recency-weighted "fresh" should dominate
    assert stats.tag_recency_weighted["fresh"] > stats.tag_recency_weighted["stale"]


def test_compute_memory_stats_top_tags_orders_by_recency_weighted():
    now = _now()
    recent = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    memories = [
        {"id": "1", "tags": ["recent_only"], "score": 0.5, "event_date": recent},
        {"id": "2", "tags": ["old_high_freq"], "score": 0.5, "event_date": old},
        {"id": "3", "tags": ["old_high_freq"], "score": 0.5, "event_date": old},
        {"id": "4", "tags": ["old_high_freq"], "score": 0.5, "event_date": old},
    ]
    stats = compute_memory_stats(memories, now_epoch=now, recency_half_life_seconds=3600)
    top = stats.top_tags(n=2)
    # Recent should win despite lower raw frequency, because of half-life weighting
    assert top[0] == "recent_only"


def test_compute_memory_stats_tag_clusters_groups_cooccurring():
    memories = [
        {"id": "1", "tags": ["a", "b"], "score": 0.5},
        {"id": "2", "tags": ["b", "c"], "score": 0.5},
        {"id": "3", "tags": ["x", "y"], "score": 0.5},
    ]
    stats = compute_memory_stats(memories, now_epoch=_now())
    # Two clusters: {a,b,c} and {x,y}
    assert len(stats.tag_clusters) == 2
    cluster_sizes = sorted(len(c) for c in stats.tag_clusters)
    assert cluster_sizes == [2, 3]


def test_compute_memory_stats_handles_missing_timestamps():
    memories = [
        {"id": "1", "tags": ["a"], "score": 0.5},
        {"id": "2", "tags": ["b"], "score": 0.5},
    ]
    stats = compute_memory_stats(memories, now_epoch=_now())
    assert stats.total_memories == 2
    assert stats.mean_age_seconds == 0.0


def test_compute_memory_stats_handles_unknown_fact_type():
    memories = [{"id": "1", "tags": [], "score": 0.5}]
    stats = compute_memory_stats(memories, now_epoch=_now())
    assert stats.fact_type_counts == {"unknown": 1}


def test_compute_memory_stats_clamps_invalid_scores():
    memories = [
        {"id": "1", "tags": [], "score": "not-a-number"},
        {"id": "2", "tags": [], "score": float("nan")},
    ]
    stats = compute_memory_stats(memories, now_epoch=_now())
    # Both fall back to 0.5, so density should be 0.5
    assert stats.signal_density == 0.5


def test_normalize_tags_handles_string():
    assert _normalize_tags("only_one") == ["only_one"]


def test_normalize_tags_handles_list():
    assert _normalize_tags(["a", "b"]) == ["a", "b"]


def test_normalize_tags_handles_none():
    assert _normalize_tags(None) == []


def test_normalize_tags_handles_set():
    out = _normalize_tags({"a", "b"})
    assert sorted(out) == ["a", "b"]


def test_recency_weight_at_zero_age_is_one():
    assert _recency_weight(0.0, 3600.0) == 1.0


def test_recency_weight_at_half_life_is_half():
    import math as m

    assert m.isclose(_recency_weight(3600.0, 3600.0), 0.5, rel_tol=1e-9)


def test_recency_weight_negative_half_life_returns_one():
    assert _recency_weight(1000.0, -1.0) == 1.0


def test_connected_components_empty():
    assert _connected_components({}) == []


def test_connected_components_orders_by_size_descending():
    adj = {
        "a": {"b"},
        "b": {"a", "c"},
        "c": {"b"},
        "x": {"y"},
        "y": {"x"},
    }
    components = _connected_components(adj)
    assert len(components) == 2
    assert len(components[0]) == 3
    assert len(components[1]) == 2
