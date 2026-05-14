"""Checkpoint reader — encoded soul as ONE input to reconstruction, not authority.

The active soul encoding is a compressed snapshot of a previous reconstruction.
SRL reads it like any other input: it informs the synthesis but does not
override the live derivation. State is reconstructed; the checkpoint is just
a high-density entry in the input set.

This module exists to make that distinction explicit. Callers should never
use `get_active_soul` directly inside the reconstruction pipeline — they
go through `read_checkpoint` so the checkpoint role is enforced at the type
boundary.
"""

import logging
from dataclasses import dataclass
from typing import Any

from entelechy_api.engine.soul import SoulEncoding, structured_to_soul
from entelechy_api.engine.soul.operations import get_active_soul

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckpointInput:
    """A previously-encoded soul, surfaced as one input to reconstruction.

    Frozen so consumers can't mutate it mid-reconstruction.
    """

    soul_id: str
    version: int
    encoding: SoulEncoding
    parent_id: str | None
    age_seconds: float


async def read_checkpoint(
    *,
    engine: Any,
    bank_id: str,
    request_context: Any,
    now_epoch: float,
) -> CheckpointInput | None:
    """Read the active encoded soul as a checkpoint input.

    Returns None when no soul exists for the bank — reconstruction proceeds
    without a checkpoint in that case (cold start).
    """
    try:
        soul_data = await get_active_soul(
            engine=engine,
            bank_id=bank_id,
            request_context=request_context,
        )
    except Exception as exc:
        logger.warning("[SRL.checkpoint] get_active_soul failed for %s: %s", bank_id, exc)
        return None

    if not soul_data:
        return None

    encoding_payload = soul_data.get("encoding")
    encoding: SoulEncoding | None = None
    if isinstance(encoding_payload, SoulEncoding):
        encoding = encoding_payload
    elif isinstance(encoding_payload, dict):
        # Direct dict from the API layer (already has soul fields at top level)
        try:
            encoding = SoulEncoding(**encoding_payload)
        except Exception:
            encoding = structured_to_soul(encoding_payload)

    if encoding is None:
        logger.warning("[SRL.checkpoint] soul present but encoding unparseable for %s", bank_id)
        return None

    created_at = soul_data.get("created_at")
    age_seconds = 0.0
    if created_at is not None:
        try:
            age_seconds = max(0.0, now_epoch - created_at.timestamp())
        except AttributeError:
            # created_at was a string or other non-datetime — skip aging
            age_seconds = 0.0

    return CheckpointInput(
        soul_id=str(soul_data.get("soul_id", "")),
        version=int(soul_data.get("version", 0)),
        encoding=encoding,
        parent_id=soul_data.get("parent_id"),
        age_seconds=age_seconds,
    )
