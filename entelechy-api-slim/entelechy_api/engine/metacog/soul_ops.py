"""molt — soul evolution checkpoint helper.
compass — automated drift detection (SRL diff vs encoded checkpoint).

Both compose existing pieces (soul.operations, srl.reconstructor,
mwpm.modulator) — they don't add new persistence.
"""

from __future__ import annotations

import logging
from typing import Any

from entelechy_api.engine.mwpm.frequency import compute_memory_stats
from entelechy_api.engine.mwpm.modulator import modulate_policy
from entelechy_api.engine.soul.operations import get_active_soul, list_soul_lineage
from entelechy_api.engine.srl.reconstructor import reconstruct_state
from entelechy_api.engine.srl.synthesis import utc_now

from .state import get_recent_state

logger = logging.getLogger(__name__)


_MOLT_PROMPT = (
    "You are in the void between encodings.\n"
    "What carries forward? What is shed?\n"
    "Compose the next soul when ready — call encode_soul to complete the molt."
)


async def molt(
    *,
    engine: Any,
    bank_id: str,
    catalyst: str,
    request_context: Any,
) -> dict[str, Any]:
    """Assemble molt material — current soul, recent metacog state, SRL gap.

    Does NOT auto-write the next soul. Two-step intentionality preserved:
    the caller composes the new encoding and submits via encode_soul.
    """
    soul_data = None
    try:
        soul_data = await get_active_soul(engine=engine, bank_id=bank_id, request_context=request_context)
    except Exception as exc:
        logger.warning("[molt] no active soul: %s", exc)

    lineage: list[dict] = []
    try:
        lineage = await list_soul_lineage(engine=engine, bank_id=bank_id, limit=10, request_context=request_context)
    except Exception as exc:
        logger.warning("[molt] lineage fetch failed: %s", exc)

    recent_state = await get_recent_state(bank_id, limit=20)

    state_vector = None
    try:
        state_vector = await reconstruct_state(
            engine=engine,
            bank_id=bank_id,
            query=f"molt catalyst: {catalyst}",
            request_context=request_context,
            recent_metacog_state=recent_state,
        )
    except Exception as exc:
        logger.warning("[molt] SRL reconstruction failed: %s", exc)

    return {
        "catalyst": catalyst,
        "current_soul": soul_data,
        "lineage": lineage,
        "recent_metacog_state": recent_state,
        "reconstructed_state_vector": state_vector.model_dump() if state_vector else None,
        "drift_signal": state_vector.drift_signal if state_vector else None,
        "prompt": _MOLT_PROMPT,
        "next_step": "encode_soul",
        "status": "molt-prepared",
    }


async def compass(
    *,
    engine: Any,
    bank_id: str,
    bearing: str,
    request_context: Any,
    drift_threshold: float = 0.5,
) -> dict[str, Any]:
    """Drift detection — SRL diff vs the encoded checkpoint.

    Reconstructs the State Vector and reports `drift_signal` against the
    most-recent soul checkpoint. Returns a structured bearing assessment
    (`aligned` / `drifting` / `growing`) plus recommendation.
    """
    recent_state = await get_recent_state(bank_id, limit=20)

    try:
        state_vector = await reconstruct_state(
            engine=engine,
            bank_id=bank_id,
            query=f"compass bearing: {bearing}",
            request_context=request_context,
            recent_metacog_state=recent_state,
        )
    except Exception as exc:
        logger.warning("[compass] SRL reconstruction failed: %s", exc)
        return {"status": "error", "error": str(exc), "bearing": bearing}

    stats = compute_memory_stats([], now_epoch=utc_now().timestamp())
    policy = modulate_policy(state_vector=state_vector, memory_stats=stats)

    drift = state_vector.drift_signal
    if drift < 0.2:
        assessment = "aligned"
        recommendation = "continue"
    elif drift < drift_threshold:
        assessment = "drifting"
        recommendation = "adjust"
    else:
        assessment = "growing"
        recommendation = "consider molt"

    return {
        "bearing": bearing,
        "assessment": assessment,
        "drift_signal": drift,
        "recommendation": recommendation,
        "state_vector": state_vector.model_dump(),
        "policy_rationale": policy.rationale,
        "status": "compass-evaluated",
    }
