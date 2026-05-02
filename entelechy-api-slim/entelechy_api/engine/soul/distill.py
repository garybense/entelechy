"""distill() — Soul-aware reflect for emergent wisdom synthesis.

distill() is categorically different from recall and reflect:
  - recall:   finds facts matching your search
  - reflect:  reasons across memories to form an answer
  - distill:  synthesizes wisdom through the soul's lens

The soul encoding shapes what distill pays attention to, what it
considers significant, and how it frames emergent patterns.

Same bank + different soul = different wisdom. This is the killer demo.
"""

import logging
from typing import Any

from entelechy_api.engine.soul.operations import get_active_soul

logger = logging.getLogger(__name__)

# Soul-aware system context injected into the reflect prompt
_DISTILL_PREAMBLE = """You are distilling wisdom from accumulated experience.

This is not recall (finding facts) or reflect (answering questions).
This is distillation: surfacing emergent patterns, earned insights,
and synthesized understanding that only becomes visible across the
full arc of accumulated experience.

{soul_context}

Approach this distillation through that identity lens. What patterns
emerge that this particular perspective would notice? What has been
learned that only makes sense now, looking back?

Be dense. Be specific. Surface what is non-obvious.
"""

_SOUL_CONTEXT_TEMPLATE = """Current Soul Encoding:
- Identity: {identity}
- Posture: {posture}
- Active: {active}
- Aesthetics: {aesthetics}
- Covenant: {covenant}

Distill through this lens. What this identity finds significant,
what it would notice across accumulated experience, what patterns
align with its active work and covenant commitments.
"""


async def distill(
    engine: Any,
    bank_id: str,
    query: str,
    *,
    context: str | None = None,
    budget: str = "high",
    max_tokens: int = 4096,
    use_soul: bool = True,
    request_context: Any,
) -> dict[str, Any]:
    """Synthesize emergent wisdom from accumulated experience through the soul's lens.

    distill() wraps reflect() with soul-aware context injection. The active
    soul encoding shapes what patterns are noticed and how they are framed.

    Args:
        engine: MemoryEngine instance
        bank_id: Target bank
        query: What to distill wisdom about
        context: Optional additional framing context
        budget: Search budget for underlying reflect ('low', 'mid', 'high')
        max_tokens: Max tokens for the distilled response
        use_soul: If True, inject soul context into reflect (default: True)
        request_context: Auth context

    Returns:
        Dict with distilled wisdom, soul version used, and reflect metadata
    """
    await engine._authenticate_tenant(request_context)

    # Get current active soul for lens injection
    soul_data = None
    soul_context_str = ""

    if use_soul:
        try:
            soul_data = await get_active_soul(
                engine=engine,
                bank_id=bank_id,
                request_context=request_context,
            )
        except Exception as e:
            logger.warning(f"[DISTILL] Could not load soul for bank {bank_id}: {e}")

    if soul_data and soul_data.get("encoding"):
        enc = soul_data["encoding"]
        soul_context_str = _SOUL_CONTEXT_TEMPLATE.format(
            identity=enc.get("identity", ""),
            posture=enc.get("posture", ""),
            active=enc.get("active", ""),
            aesthetics=enc.get("aesthetics", ""),
            covenant=enc.get("covenant", ""),
        )
        logger.info(
            f"[DISTILL] Using soul v{soul_data['version']} "
            f"for bank {bank_id} distillation"
        )
    else:
        logger.info(f"[DISTILL] No soul found for {bank_id}, distilling without lens")

    # Build the soul-shaped context for reflect
    soul_preamble = _DISTILL_PREAMBLE.format(
        soul_context=soul_context_str if soul_context_str else
        "(No soul encoding found — distilling without identity lens)"
    )

    full_context = soul_preamble
    if context:
        full_context = f"{soul_preamble}\n\nAdditional context: {context}"

    # Call reflect_async with soul-shaped context
    try:
        reflect_result = await engine.reflect_async(
            bank_id=bank_id,
            query=query,
            context=full_context,
            max_tokens=max_tokens,
            request_context=request_context,
        )
    except Exception as e:
        logger.error(f"[DISTILL] Reflect failed: {e}", exc_info=True)
        raise

    return {
        "query": query,
        "wisdom": getattr(reflect_result, 'response', None) or getattr(reflect_result, 'content', None) or str(reflect_result),
        "soul_version": soul_data["version"] if soul_data else None,
        "soul_id": soul_data["soul_id"] if soul_data else None,
        "bank_id": bank_id,
        "budget": budget,
        "lens_applied": bool(soul_context_str),
        "status": "distilled",
    }
