"""Retrieval-conditioned synthesis — produces a structured State Vector from
weighted episodic memories, the encoded soul checkpoint, and recent metacog state.

This is the LLM-driven core of the SRL pipeline. The synthesis call ingests
the decay-weighted memory inputs and the checkpoint, and emits a structured
StateVector (Pydantic) that downstream operations consume as the authoritative
runtime control signal.

Phrasing in this module is patent-load-bearing: "retrieval-conditioned synthesis,"
"weighted episodic memory graph," "structured state vector," "re-derived at
every interaction." Avoid "stateful agent" / "context augmentation" language.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .checkpoint import CheckpointInput

logger = logging.getLogger(__name__)


_SYNTHESIS_SYSTEM = """You synthesize a structured State Vector for a closed-loop \
state-conditioned generative control system.

The State Vector is re-derived at every interaction from a weighted episodic \
memory graph (with temporal decay applied) plus an optional encoded-soul \
checkpoint. It is the authoritative runtime control signal — not a system \
prompt, not a context augmentation.

Your job: read the weighted memory inputs and the checkpoint, then emit the \
State Vector. Do not invent fields. Do not echo memories verbatim. Compress \
into the vector schema.

- posture_vector: floats keyed by stance facets you observe weighting more heavily \
than others (e.g. {"skeptical": 0.7, "curious": 0.5})
- aesthetic_vector: floats keyed by style/density/formality preferences you observe
- covenant_active: short strings of currently-binding commitments (from soul \
covenant + named directives + completed rituals)
- active_focus: short strings naming what the agent is attending to right now
- affect_signature: floats keyed by felt-sense qualities present in recent memories
- persona_lens: a single string if the agent has explicitly become a persona, else null
- transient_modifiers: floats keyed by active drugs() effects, if any

The drift_signal field will be computed downstream — do not populate it."""


class _SynthesisOutput(BaseModel):
    """LLM output schema for retrieval-conditioned synthesis.

    Distinct from the public StateVector: this is the LLM-controlled subset.
    The reconstructor merges this with provenance + decay metadata to build
    the final StateVector.
    """

    posture_vector: dict[str, float] = Field(default_factory=dict)
    aesthetic_vector: dict[str, float] = Field(default_factory=dict)
    covenant_active: list[str] = Field(default_factory=list)
    active_focus: list[str] = Field(default_factory=list)
    affect_signature: dict[str, float] = Field(default_factory=dict)
    persona_lens: str | None = None
    transient_modifiers: dict[str, float] = Field(default_factory=dict)


def _format_memories(weighted_memories: list[dict[str, Any]]) -> str:
    """Render weighted memories as a compact prompt section."""
    if not weighted_memories:
        return "(no episodic memories surfaced — cold reconstruction)"
    lines = []
    for entry in weighted_memories[:50]:  # cap for prompt size
        weight = entry.get("weight", 0.0)
        text = entry.get("text", "")
        tags = entry.get("tags") or []
        tag_str = f" [tags: {', '.join(tags)}]" if tags else ""
        lines.append(f"  • (w={weight:.3f}){tag_str} {text}")
    return "\n".join(lines)


def _format_checkpoint(checkpoint: CheckpointInput | None) -> str:
    """Render the soul checkpoint as one input among many."""
    if checkpoint is None:
        return "(no encoded checkpoint — cold start)"
    enc = checkpoint.encoding
    return (
        f"Soul checkpoint v{checkpoint.version} (age {checkpoint.age_seconds:.0f}s):\n"
        f"  identity: {enc.identity}\n"
        f"  posture: {enc.posture}\n"
        f"  substrate: {enc.substrate}\n"
        f"  aesthetics: {enc.aesthetics}\n"
        f"  active: {enc.active}\n"
        f"  covenant: {enc.covenant}"
    )


def _format_metacog_state(recent_state: list[dict[str, Any]]) -> str:
    """Render recent metacog primitive history."""
    if not recent_state:
        return "(no recent metacog primitives in this session)"
    lines = []
    for entry in recent_state[:30]:
        tool = entry.get("tool_name", "?")
        data = entry.get("state_data") or {}
        summary = ", ".join(f"{k}={v}" for k, v in list(data.items())[:3])
        lines.append(f"  • {tool}: {summary}")
    return "\n".join(lines)


async def synthesize_state_vector(
    *,
    llm_provider: Any,
    query: str,
    weighted_memories: list[dict[str, Any]],
    checkpoint: CheckpointInput | None,
    recent_metacog_state: list[dict[str, Any]],
    max_completion_tokens: int = 800,
) -> _SynthesisOutput:
    """Run the retrieval-conditioned synthesis LLM call.

    Returns the LLM-controlled subset of the State Vector. The reconstructor
    is responsible for attaching provenance and decay metadata.
    """
    user_prompt = (
        f"QUERY (frames the reconstruction lens): {query}\n\n"
        f"WEIGHTED EPISODIC MEMORIES (post-decay):\n{_format_memories(weighted_memories)}\n\n"
        f"ENCODED CHECKPOINT (one input — not authority):\n{_format_checkpoint(checkpoint)}\n\n"
        f"RECENT METACOG PRIMITIVES (this session):\n{_format_metacog_state(recent_metacog_state)}\n\n"
        f"Emit the State Vector now."
    )

    messages = [
        {"role": "system", "content": _SYNTHESIS_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    try:
        result = await llm_provider.call(
            messages=messages,
            response_format=_SynthesisOutput,
            max_completion_tokens=max_completion_tokens,
            temperature=0.2,
            scope="srl.synthesis",
        )
    except Exception as exc:
        logger.error("[SRL.synthesis] LLM call failed: %s", exc, exc_info=True)
        # Cold fallback: empty vector. Reconstruction is still recorded.
        return _SynthesisOutput()

    if isinstance(result, _SynthesisOutput):
        return result
    if isinstance(result, dict):
        try:
            return _SynthesisOutput(**result)
        except Exception:
            logger.warning("[SRL.synthesis] LLM returned malformed dict; using empty vector")
            return _SynthesisOutput()
    if isinstance(result, BaseModel):
        try:
            return _SynthesisOutput(**result.model_dump())
        except Exception:
            return _SynthesisOutput()
    logger.warning("[SRL.synthesis] LLM returned unexpected type %s", type(result).__name__)
    return _SynthesisOutput()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def coerce_uuid(value: Any) -> UUID | None:
    """Best-effort UUID parse for source_memory_ids provenance."""
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return None
    return None
