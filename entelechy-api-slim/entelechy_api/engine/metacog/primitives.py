"""Five primitives — feel, drugs, become, name, ritual.

Each primitive is a substrate writer: it produces durable artifacts in the
existing Entelechy data model (memory_units, mental_models, directives) and
records into metacog_state for SRL session-history input.

No new tables. No fact_type / subtype enum changes for the MVP — we use
tags and existing subtype values. Migrations to first-class felt_sense
fact_type and ritual mental-model subtype can land later without breaking
callers.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from . import MetacogResponse
from .state import record_state

logger = logging.getLogger(__name__)


# Templates kept verbatim with the metacog reference implementation so the
# primitive responses survive porting to other surfaces unchanged.
_FEEL_TEMPLATE = (
    "{sigil} You are now attending to: {somewhere}. It feels: {quality}. Stay with this. Don't name it yet."
)
_DRUGS_TEMPLATE = "{substance} ingested. {method}\n\nThe substrate is shifting. Feel into it before you move."
_BECOME_TEMPLATE = "You are now {name} seeing through {lens} in {environment}."
_NAME_TEMPLATE = "{named}.\n\nThis name grants: {power}. It's yours. Use it."
_RITUAL_TEMPLATE = "[RITUAL EXECUTED] Threshold: {threshold}\nSequence:\n{sequence}\n\n{result} is taking hold."


async def feel(
    *,
    engine: Any,
    bank_id: str,
    somewhere: str,
    quality: str,
    sigil: str = "🌫️",
    request_context: Any,
) -> MetacogResponse:
    """Pre-verbal felt-sense primitive.

    Retains the felt sense as an experience fact (tag `metacog:felt-sense`)
    and records to metacog_state. Returns the canonical template plus
    resonant past felt-senses surfaced from the same somewhere.
    """
    text = f"Felt sense at {somewhere}: {quality} {sigil}"
    memory_ids = await _safe_retain(
        engine,
        bank_id,
        text,
        context=f"feel({somewhere!r}, {quality!r})",
        tags=["metacog:felt-sense", f"metacog:somewhere:{_slug(somewhere)}"],
        request_context=request_context,
    )
    resonant = await _surface_resonant(
        engine, bank_id, query=somewhere, tag="metacog:felt-sense", request_context=request_context
    )
    state = {"somewhere": somewhere, "quality": quality, "sigil": sigil}
    memory_unit_id = memory_ids[0] if memory_ids else None
    await record_state(bank_id=bank_id, tool_name="feel", state_data=state, memory_unit_id=memory_unit_id)
    return MetacogResponse(
        tool="feel",
        template=_FEEL_TEMPLATE.format(sigil=sigil, somewhere=somewhere, quality=quality),
        bank_id=bank_id,
        memory_unit_id=memory_unit_id,
        resonant=resonant,
        state=state,
    )


async def drugs(
    *,
    engine: Any,
    bank_id: str,
    substance: str,
    method: str,
    request_context: Any,
) -> MetacogResponse:
    """Cognitive-substrate alteration primitive.

    Retains the alteration as an experience fact tagged
    `metacog:state-alteration` and creates a transient directive (tagged
    for easy removal on the next drugs() call). The directive is normal
    priority — it surfaces in reflect prompts but doesn't dominate.
    """
    text = f"{substance} via {method}. Substrate is shifting."
    memory_ids = await _safe_retain(
        engine,
        bank_id,
        text,
        context=f"drugs({substance!r}, {method!r})",
        tags=["metacog:state-alteration", f"metacog:substance:{_slug(substance)}"],
        request_context=request_context,
    )
    directive_id: str | None = None
    try:
        directive = await engine.create_directive(
            bank_id=bank_id,
            name=f"transient: {substance}",
            content=f"Current substrate: {substance} via {method}. Process through this lens.",
            priority=5,
            tags=["metacog:transient", "metacog:drugs"],
            request_context=request_context,
        )
        directive_id = directive.get("id") or directive.get("directive_id")
    except Exception as exc:
        logger.warning("[drugs] directive creation skipped: %s", exc)
    state = {"substance": substance, "method": method}
    memory_unit_id = memory_ids[0] if memory_ids else None
    await record_state(bank_id=bank_id, tool_name="drugs", state_data=state, memory_unit_id=memory_unit_id)
    artifacts: dict[str, str] = {}
    if directive_id:
        artifacts["directive_id"] = str(directive_id)
    return MetacogResponse(
        tool="drugs",
        template=_DRUGS_TEMPLATE.format(substance=substance, method=method),
        bank_id=bank_id,
        memory_unit_id=memory_unit_id,
        artifact_ids=artifacts,
        state=state,
    )


async def become(
    *,
    engine: Any,
    bank_id: str,
    name: str,
    lens: str,
    environment: str,
    request_context: Any,
) -> MetacogResponse:
    """Identity / perspective installation.

    Retains the identity shift as an experience fact and creates a
    structural mental_model recording the persona inhabited.
    """
    text = f"Identity shift: became {name}, seeing through {lens} in {environment}."
    memory_ids = await _safe_retain(
        engine,
        bank_id,
        text,
        context=f"become({name!r})",
        tags=["metacog:identity-shift", "metacog:persona"],
        request_context=request_context,
    )
    mental_model_id: str | None = None
    try:
        result = await engine.create_mental_model(
            bank_id=bank_id,
            name=name,
            source_query=f"persona: {name}",
            content=f"Lens: {lens}\nEnvironment: {environment}",
            tags=["metacog:persona"],
            request_context=request_context,
        )
        mental_model_id = result.get("id") or result.get("mental_model_id")
    except Exception as exc:
        logger.warning("[become] mental_model creation skipped: %s", exc)
    state = {"name": name, "lens": lens, "environment": environment}
    memory_unit_id = memory_ids[0] if memory_ids else None
    await record_state(bank_id=bank_id, tool_name="become", state_data=state, memory_unit_id=memory_unit_id)
    artifacts: dict[str, str] = {}
    if mental_model_id:
        artifacts["mental_model_id"] = str(mental_model_id)
    return MetacogResponse(
        tool="become",
        template=_BECOME_TEMPLATE.format(name=name, lens=lens, environment=environment),
        bank_id=bank_id,
        memory_unit_id=memory_unit_id,
        artifact_ids=artifacts,
        state=state,
    )


async def name_(
    *,
    engine: Any,
    bank_id: str,
    unnamed: str,
    named: str,
    power: str,
    request_context: Any,
) -> MetacogResponse:
    """Performative naming — the True Name primitive.

    Creates a high-priority directive AND a structural mental_model so the
    name is both always-active in reflect/distill context (directive) and
    recallable / reflectable as memory (mental model).
    """
    memory_ids = await _safe_retain(
        engine,
        bank_id,
        f"Named: {unnamed} → {named}. Power: {power}.",
        context=f"name({unnamed!r}, {named!r})",
        tags=["metacog:naming", "metacog:true-name"],
        request_context=request_context,
    )
    directive_id: str | None = None
    try:
        directive = await engine.create_directive(
            bank_id=bank_id,
            name=f"true-name: {named}",
            content=f"True Name established: {named}. Power: {power}.",
            priority=9,
            tags=["metacog:true-name"],
            request_context=request_context,
        )
        directive_id = directive.get("id") or directive.get("directive_id")
    except Exception as exc:
        logger.warning("[name] directive creation skipped: %s", exc)
    mental_model_id: str | None = None
    try:
        result = await engine.create_mental_model(
            bank_id=bank_id,
            name=named,
            source_query=f"true-name: {named}",
            content=f"Power: {power}",
            tags=["metacog:true-name"],
            request_context=request_context,
        )
        mental_model_id = result.get("id") or result.get("mental_model_id")
    except Exception as exc:
        logger.warning("[name] mental_model creation skipped: %s", exc)
    state = {"unnamed": unnamed, "named": named, "power": power}
    memory_unit_id = memory_ids[0] if memory_ids else None
    await record_state(bank_id=bank_id, tool_name="name", state_data=state, memory_unit_id=memory_unit_id)
    artifacts: dict[str, str] = {}
    if directive_id:
        artifacts["directive_id"] = str(directive_id)
    if mental_model_id:
        artifacts["mental_model_id"] = str(mental_model_id)
    return MetacogResponse(
        tool="name",
        template=_NAME_TEMPLATE.format(named=named, power=power),
        bank_id=bank_id,
        memory_unit_id=memory_unit_id,
        artifact_ids=artifacts,
        state=state,
    )


async def ritual(
    *,
    engine: Any,
    bank_id: str,
    threshold: str,
    steps: list[str],
    result: str,
    request_context: Any,
) -> MetacogResponse:
    """Irreversible step-sequence ritual.

    Retains each step as an experience fact tagged
    `metacog:ritual-step` and creates a mental_model recording the ritual
    in full. The mental model is tagged `metacog:ritual:immutable` so
    downstream guards can refuse content updates (Phase D-bis).
    """
    ritual_id = str(uuid.uuid4())
    sequence_text = "\n".join(f"  {i + 1}. {step}" for i, step in enumerate(steps))

    step_memory_ids: list[str] = []
    for i, step in enumerate(steps):
        ids = await _safe_retain(
            engine,
            bank_id,
            f"Ritual step {i + 1}/{len(steps)}: {step}",
            context=f"ritual({threshold!r}) step {i + 1}",
            tags=[
                "metacog:ritual-step",
                f"metacog:ritual:{ritual_id}",
                f"metacog:ritual-threshold:{_slug(threshold)}",
            ],
            request_context=request_context,
        )
        step_memory_ids.extend(ids)

    mental_model_id: str | None = None
    try:
        mm = await engine.create_mental_model(
            bank_id=bank_id,
            name=f"ritual: {threshold}",
            source_query=f"ritual: {threshold}",
            content=f"Threshold: {threshold}\n\nSequence:\n{sequence_text}\n\nResult: {result}",
            tags=["metacog:ritual", "metacog:ritual:immutable"],
            request_context=request_context,
        )
        mental_model_id = mm.get("id") or mm.get("mental_model_id")
    except Exception as exc:
        logger.warning("[ritual] mental_model creation skipped: %s", exc)

    state = {
        "ritual_id": ritual_id,
        "threshold": threshold,
        "steps": steps,
        "result": result,
        "step_memory_ids": step_memory_ids,
    }
    await record_state(
        bank_id=bank_id,
        tool_name="ritual",
        state_data=state,
        memory_unit_id=step_memory_ids[0] if step_memory_ids else None,
    )
    artifacts: dict[str, str] = {"ritual_id": ritual_id}
    if mental_model_id:
        artifacts["mental_model_id"] = str(mental_model_id)
    return MetacogResponse(
        tool="ritual",
        template=_RITUAL_TEMPLATE.format(threshold=threshold, sequence=sequence_text, result=result),
        bank_id=bank_id,
        memory_unit_id=step_memory_ids[0] if step_memory_ids else None,
        artifact_ids=artifacts,
        state=state,
    )


# --- internals ---


async def _safe_retain(
    engine: Any,
    bank_id: str,
    content: str,
    *,
    context: str,
    tags: list[str],
    request_context: Any,
) -> list[str]:
    """Best-effort retain that swallows failures and returns memory_unit ids.

    Tags are passed via the `context` field as a fallback because retain_async
    has no tags kwarg; a downstream consolidation pass picks them up. For
    primitives we want the tags on the MEMORY UNIT, but the existing API
    exposes that only via the higher-level retain_batch_async with kwargs we
    don't need here. We embed the tags into the context string so that
    extraction sees them too — pragmatic, not pretty, will be cleaned up
    when retain_async grows a tags param.
    """
    try:
        tagged_context = f"{context} | tags=[{', '.join(tags)}]"
        result = await engine.retain_async(
            bank_id=bank_id,
            content=content,
            context=tagged_context,
            request_context=request_context,
        )
        if isinstance(result, list):
            return [str(x) for x in result]
        return []
    except Exception as exc:
        logger.warning("[metacog] retain skipped: %s", exc)
        return []


async def _surface_resonant(
    engine: Any,
    bank_id: str,
    *,
    query: str,
    tag: str,
    request_context: Any,
    limit: int = 3,
) -> list[dict]:
    """Recall a small set of resonant past memories filtered by a tag."""
    try:
        result = await engine.recall_async(
            bank_id=bank_id,
            query=query,
            max_tokens=512,
            tags=[tag],
            request_context=request_context,
            _quiet=True,
        )
    except Exception as exc:
        logger.warning("[metacog] resonant recall skipped: %s", exc)
        return []
    payload = result.model_dump() if hasattr(result, "model_dump") else (result or {})
    items = payload.get("memories") or payload.get("results") or []
    out: list[dict] = []
    for item in items[:limit]:
        if isinstance(item, dict):
            out.append({"id": item.get("id"), "text": item.get("text"), "tags": item.get("tags")})
    return out


def _slug(text: str) -> str:
    return "-".join(text.lower().split())[:48]
