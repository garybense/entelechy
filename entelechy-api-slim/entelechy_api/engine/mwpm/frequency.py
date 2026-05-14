"""Memory frequency / recency / semantic-clustering analysis for MWPM.

Computes the statistics that the modulator uses to derive PolicyParams.
Pure functions — they consume an already-retrieved memory list and emit
a MemoryStats record. No I/O.

The semantic-clustering layer here is intentionally simple: tag co-occurrence
within memory units, surfaced as connected components. Richer clustering
(embedding-space k-means) is a Phase G/post-MVP refinement; it would require
running pgvector queries which is out of scope for the MWPM core.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from . import MemoryStats


def compute_memory_stats(
    memories: Iterable[dict[str, Any]],
    *,
    now_epoch: float,
    recency_half_life_seconds: float = 86400.0,
) -> MemoryStats:
    """Aggregate frequency / recency / cluster statistics over a memory list.

    Args:
        memories: Iterable of memory-unit dicts as returned by recall_async.
            Expected keys (best-effort): id, text, tags, score, fact_type,
            event_date / mentioned_at / created_at.
        now_epoch: Reference time (UTC seconds-since-epoch) for recency math.
        recency_half_life_seconds: Half-life for the recency-weighted tag
            frequency. Tags that appear in older memories contribute less.

    Returns:
        MemoryStats — feeds directly into MWPM modulator.
    """
    materialized = list(memories)
    if not materialized:
        return MemoryStats()

    tag_frequency: dict[str, int] = {}
    tag_recency_weighted: dict[str, float] = {}
    fact_type_counts: dict[str, int] = {}
    ages: list[float] = []
    scores: list[float] = []
    tag_cooccurrence: dict[str, set[str]] = {}

    for mem in materialized:
        tags = _normalize_tags(mem.get("tags"))
        fact_type = str(mem.get("fact_type") or "").strip() or "unknown"
        fact_type_counts[fact_type] = fact_type_counts.get(fact_type, 0) + 1

        age = _memory_age_seconds(mem, now_epoch)
        ages.append(age)
        recency_weight = _recency_weight(age, recency_half_life_seconds)

        score = _safe_score(mem)
        scores.append(score)

        for tag in tags:
            tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
            tag_recency_weighted[tag] = tag_recency_weighted.get(tag, 0.0) + recency_weight

        # Co-occurrence: tag pairs within the same memory
        for tag in tags:
            cooc = tag_cooccurrence.setdefault(tag, set())
            for other in tags:
                if other != tag:
                    cooc.add(other)

    mean_age_seconds = sum(ages) / len(ages) if ages else 0.0
    signal_density = sum(scores) / len(scores) if scores else 0.0
    tag_clusters = _connected_components(tag_cooccurrence)

    return MemoryStats(
        total_memories=len(materialized),
        tag_frequency=tag_frequency,
        tag_recency_weighted=tag_recency_weighted,
        tag_clusters=tag_clusters,
        mean_age_seconds=mean_age_seconds,
        fact_type_counts=fact_type_counts,
        signal_density=signal_density,
    )


# --- internals ---


def _normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, (list, tuple, set)):
        return [str(t) for t in raw if t]
    return []


def _memory_age_seconds(mem: dict[str, Any], now_epoch: float) -> float:
    for key in ("event_date", "mentioned_at", "created_at", "occurred_start"):
        ts = mem.get(key)
        if ts is None:
            continue
        epoch = _to_epoch(ts)
        if epoch is None:
            continue
        delta = now_epoch - epoch
        if math.isnan(delta) or math.isinf(delta) or delta < 0:
            return 0.0
        return delta
    return 0.0


def _to_epoch(ts: Any) -> float | None:
    if hasattr(ts, "timestamp"):
        try:
            return float(ts.timestamp())
        except Exception:
            return None
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        from datetime import datetime

        try:
            return datetime.fromisoformat(ts).timestamp()
        except ValueError:
            return None
    return None


def _safe_score(mem: dict[str, Any]) -> float:
    raw = mem.get("rerank_score") or mem.get("score") or 0.5
    try:
        score = float(raw)
    except (TypeError, ValueError):
        return 0.5
    if math.isnan(score) or math.isinf(score):
        return 0.5
    return max(0.0, min(1.0, score))


def _recency_weight(age_seconds: float, half_life_seconds: float) -> float:
    if half_life_seconds <= 0:
        return 1.0
    return 2.0 ** (-max(0.0, age_seconds) / half_life_seconds)


def _connected_components(adjacency: dict[str, set[str]]) -> list[list[str]]:
    """Tag-cooccurrence connected components.

    Returns lists sorted by size descending; tags within a component sorted
    lexicographically for stable output.
    """
    if not adjacency:
        return []

    visited: set[str] = set()
    components: list[list[str]] = []

    for start in adjacency:
        if start in visited:
            continue
        # BFS over the component
        stack = [start]
        component: list[str] = []
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adjacency.get(node, ()):
                if neighbor not in visited:
                    stack.append(neighbor)
        component.sort()
        components.append(component)

    components.sort(key=lambda c: (-len(c), c[0] if c else ""))
    return components
