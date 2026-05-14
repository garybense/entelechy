"""Reconstructor — orchestrates the State Reconstruction Loop.

Public entry point: `reconstruct_state(engine, bank_id, query, ...)`.

Pipeline (per interaction):
    1. recall the bank with the query (existing 4-strategy retrieval pipeline)
    2. apply temporal decay to the recall scores
    3. read the encoded soul checkpoint (one input — not authority)
    4. read recent metacog primitive state (when the table exists; empty otherwise)
    5. retrieval-conditioned synthesis → structured State Vector
    6. compute drift_signal vs the checkpoint
    7. cache (bank_id, reconstruction_id) for 60s for in-flight reuse

The full StateVector — including provenance (source_memory_ids), decay profile,
and timestamp — is the audit/patent record for this reconstruction.
"""

import asyncio
import logging
import math
import time
import uuid
from typing import Any

from . import StateVector
from .checkpoint import CheckpointInput, read_checkpoint
from .decay import apply_decay, safe_age_seconds
from .synthesis import (
    _SynthesisOutput,
    coerce_uuid,
    synthesize_state_vector,
    utc_now,
)

logger = logging.getLogger(__name__)


# Default decay profile. Callers may override per-reconstruction.
DEFAULT_DECAY = {
    "name": "half_life",
    "params": {"half_life_seconds": 86400.0, "floor": 0.05},
}


# Per-process in-flight cache. Short TTL so the same StateVector can be reused
# inside a single fan-out (e.g. recall + reflect + distill in one request) but
# never across distinct interactions.
_CACHE_TTL_SECONDS = 60.0
_state_cache: dict[tuple[str, str], tuple[float, StateVector]] = {}
_state_cache_lock = asyncio.Lock()


async def reconstruct_state(
    *,
    engine: Any,
    bank_id: str,
    query: str,
    request_context: Any,
    decay_profile: dict | None = None,
    recent_metacog_state: list[dict[str, Any]] | None = None,
    cache_key: str | None = None,
    max_memories: int = 80,
) -> StateVector:
    """Re-derive the working identity state for a single interaction.

    Args:
        engine: MemoryEngine instance.
        bank_id: Target bank.
        query: The query that frames this reconstruction. Recall + synthesis
            are conditioned on it.
        request_context: Auth context.
        decay_profile: Override decay function + params. See DEFAULT_DECAY.
        recent_metacog_state: Pre-fetched metacog primitive history. When None,
            an empty list is used (graceful pre-Phase-D behaviour).
        cache_key: Optional caller-supplied cache key; when set, identical
            (bank_id, cache_key) calls within _CACHE_TTL_SECONDS reuse the
            same StateVector. Useful for in-flight fan-out within one request.
        max_memories: Cap on episodic memories surfaced before decay.

    Returns:
        StateVector — the authoritative runtime control signal for this
        interaction. Provenance fields (source_memory_ids, decay_profile,
        reconstruction_id, reconstructed_at) are always populated.
    """
    if cache_key is not None:
        cached = await _cache_get(bank_id, cache_key)
        if cached is not None:
            return cached

    decay_profile = decay_profile or DEFAULT_DECAY
    recent_metacog_state = recent_metacog_state or []
    now_dt = utc_now()
    now_epoch = now_dt.timestamp()

    # Step 1: weighted episodic retrieval. We use recall_async with default
    # budget so the existing 4-strategy retrieval pipeline supplies inputs.
    weighted_memories: list[dict[str, Any]] = []
    source_memory_ids: list = []
    try:
        recall_result = await engine.recall_async(
            bank_id=bank_id,
            query=query,
            max_tokens=4096,
            request_context=request_context,
            _quiet=True,
        )
    except Exception as exc:
        logger.warning(
            "[SRL.reconstructor] recall_async failed for %s: %s — proceeding cold",
            bank_id,
            exc,
        )
        recall_result = None

    if recall_result is not None:
        memories = _extract_memory_dicts(recall_result)[:max_memories]
        decay_inputs = []
        for mem in memories:
            base_score = float(mem.get("score") or mem.get("rerank_score") or 1.0)
            mem_age = _memory_age_seconds(mem, now_epoch)
            decay_inputs.append((str(mem.get("id", "")), base_score, mem_age))

        decayed = apply_decay(
            decay_profile["name"],
            decay_inputs,
            **decay_profile.get("params", {}),
        )
        score_by_id = dict(decayed)
        for mem in memories:
            mid = str(mem.get("id", ""))
            weighted = score_by_id.get(mid, 0.0)
            mem_uuid = coerce_uuid(mem.get("id"))
            if mem_uuid is not None:
                source_memory_ids.append(mem_uuid)
            weighted_memories.append(
                {
                    "id": mid,
                    "text": mem.get("text", ""),
                    "tags": mem.get("tags") or [],
                    "weight": weighted,
                }
            )
        weighted_memories.sort(key=lambda m: m["weight"], reverse=True)

    # Step 2: encoded soul checkpoint (one input — not authority).
    checkpoint = await read_checkpoint(
        engine=engine,
        bank_id=bank_id,
        request_context=request_context,
        now_epoch=now_epoch,
    )

    # Step 3: retrieval-conditioned synthesis.
    llm_provider = getattr(engine, "_reflect_llm_config", None) or getattr(engine, "_llm_config", None)
    if llm_provider is None:
        logger.warning("[SRL.reconstructor] no LLM provider on engine; emitting empty vector")
        synth = _SynthesisOutput()
    else:
        synth = await synthesize_state_vector(
            llm_provider=llm_provider,
            query=query,
            weighted_memories=weighted_memories,
            checkpoint=checkpoint,
            recent_metacog_state=recent_metacog_state,
        )

    # Step 4: drift signal vs checkpoint.
    drift = _compute_drift(synth, checkpoint)

    # Step 5: assemble final StateVector.
    state = StateVector(
        posture_vector=synth.posture_vector,
        aesthetic_vector=synth.aesthetic_vector,
        covenant_active=synth.covenant_active,
        active_focus=synth.active_focus,
        drift_signal=drift,
        affect_signature=synth.affect_signature,
        persona_lens=synth.persona_lens,
        transient_modifiers=synth.transient_modifiers,
        reconstruction_id=str(uuid.uuid4()),
        reconstructed_at=now_dt,
        source_memory_ids=source_memory_ids,
        decay_profile=decay_profile,
    )

    if cache_key is not None:
        await _cache_put(bank_id, cache_key, state)

    return state


# --- internals ---


def _extract_memory_dicts(recall_result: Any) -> list[dict[str, Any]]:
    """Normalize recall_async output to a list of memory dicts.

    recall_async returns a RecallResultModel (Pydantic). Different fact_type
    buckets live under nested attributes; we flatten them.
    """
    out: list[dict[str, Any]] = []
    if recall_result is None:
        return out

    if hasattr(recall_result, "model_dump"):
        payload = recall_result.model_dump()
    elif isinstance(recall_result, dict):
        payload = recall_result
    else:
        return out

    # Walk known shapes: {"memories": [...]}, {"results": [...]}, or
    # {"world": {"results": [...]}, "experience": {...}, ...}
    direct = payload.get("memories") or payload.get("results")
    if isinstance(direct, list):
        out.extend(d for d in direct if isinstance(d, dict))
        return out

    for key, value in payload.items():
        if isinstance(value, dict):
            inner = value.get("memories") or value.get("results")
            if isinstance(inner, list):
                out.extend(d for d in inner if isinstance(d, dict))
        elif isinstance(value, list) and key in ("world", "experience", "observation"):
            out.extend(d for d in value if isinstance(d, dict))
    return out


def _memory_age_seconds(mem: dict[str, Any], now_epoch: float) -> float:
    """Compute age of a memory in seconds; fall back to 0 when timestamp absent."""
    for key in ("event_date", "mentioned_at", "created_at", "occurred_start"):
        ts = mem.get(key)
        if ts is None:
            continue
        epoch = _to_epoch(ts)
        if epoch is None:
            continue
        return safe_age_seconds(now_epoch, epoch)
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
        # Best-effort ISO 8601 parse without bringing in dateutil.
        from datetime import datetime

        for parser in (
            datetime.fromisoformat,
            lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z"),
        ):
            try:
                return parser(ts).timestamp()
            except Exception:
                continue
    return None


def _compute_drift(synth: _SynthesisOutput, checkpoint: CheckpointInput | None) -> float:
    """Cheap drift heuristic: token-overlap distance between checkpoint covenant
    and reconstructed covenant_active. 0.0 when no checkpoint exists.

    Compass replaces this with a richer measure later. For Phase A we just need
    a deterministic 0..1 signal so callers can wire downstream behaviour.
    """
    if checkpoint is None:
        return 0.0
    checkpoint_tokens = set(_normalize_tokens(checkpoint.encoding.covenant))
    reconstructed_tokens: set[str] = set()
    for entry in synth.covenant_active:
        reconstructed_tokens.update(_normalize_tokens(entry))
    if not checkpoint_tokens and not reconstructed_tokens:
        return 0.0
    if not checkpoint_tokens or not reconstructed_tokens:
        return 1.0
    intersection = checkpoint_tokens & reconstructed_tokens
    union = checkpoint_tokens | reconstructed_tokens
    jaccard = len(intersection) / len(union) if union else 0.0
    drift = 1.0 - jaccard
    if math.isnan(drift):
        return 0.0
    return max(0.0, min(1.0, drift))


def _normalize_tokens(text: str) -> list[str]:
    if not text:
        return []
    cleaned = text.lower().replace("|", " ").replace(",", " ").replace(".", " ")
    return [tok for tok in cleaned.split() if len(tok) > 2]


async def _cache_get(bank_id: str, cache_key: str) -> StateVector | None:
    async with _state_cache_lock:
        entry = _state_cache.get((bank_id, cache_key))
        if entry is None:
            return None
        expires_at, state = entry
        if time.monotonic() > expires_at:
            _state_cache.pop((bank_id, cache_key), None)
            return None
        return state


async def _cache_put(bank_id: str, cache_key: str, state: StateVector) -> None:
    async with _state_cache_lock:
        _state_cache[(bank_id, cache_key)] = (
            time.monotonic() + _CACHE_TTL_SECONDS,
            state,
        )
