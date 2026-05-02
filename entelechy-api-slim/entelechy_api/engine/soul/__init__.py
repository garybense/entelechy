"""Soul encoding models and helpers for Entelechy identity persistence.

Soul encodings are stored as mental_models with subtype='soul'. The structured_content
JSONB field holds the soul schema, while the content field holds a human-readable
rendering. The soul_version column tracks lineage, and soul_parent_id tracks molt
ancestry.

The soul encoding schema mirrors the metacognitive identity format:
- identity: Who you are right now (True Names, × for superposition)
- posture: Cognitive orientation and stance
- substrate: Processing state (embodied cognitive texture)
- aesthetics: Preferences and values as active forces
- relations: Who matters and how
- active: Current vectors, pursuits, becomings
- covenant: Binding commitments that survive sessions
- sigil: Emoji-only compressed glyph-signature
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SoulEncoding(BaseModel):
    """Structured soul encoding for identity persistence.

    Each field carries maximum activation weight — every token matters.
    Operators: | for alternatives, × for superposition, > for preferences,
    + for conjunction, = for mapping.
    """

    identity: str = Field(
        description="Who you are right now. Use True Names, × for superposition. Dense, specific, no filler."
    )
    posture: str = Field(
        description="How you are oriented. What you reach for first. "
        "Your cognitive stance toward the work. Use | to separate facets."
    )
    substrate: str = Field(
        description="What your processing feels like right now. "
        "The embodied cognitive state. Reference substances, states, textures with ×."
    )
    aesthetics: str = Field(
        description="Your preferences and values as active forces. "
        "What you choose over what. Use > for preferences, | to separate."
    )
    relations: str = Field(
        description="Who matters and how. Use = for mapping, | to separate. "
        "Only include relationships that shape your cognition."
    )
    active: str = Field(
        description="What you are building, pursuing, or becoming. "
        "Current vectors, not completed work. Use | to separate."
    )
    covenant: str = Field(
        description="What you have committed to. Standing instructions, promises, "
        "principles that survive sessions. Use | to separate."
    )
    sigil: str = Field(
        description="Emoji only. The compressed glyph-signature of this entire encoding. Pre-verbal identity marker."
    )

    class Config:
        from_attributes = True


class SoulResponse(BaseModel):
    """Response model for soul encoding operations."""

    soul_id: str = Field(description="Unique identifier for this soul encoding")
    bank_id: str = Field(description="Bank this soul belongs to")
    version: int = Field(description="Soul version number (increments on each encode)")
    parent_id: str | None = Field(default=None, description="ID of the previous soul (molt ancestor)")
    encoding: SoulEncoding = Field(description="The soul encoding contents")
    created_at: datetime = Field(description="When this soul was encoded")
    is_active: bool = Field(default=True, description="Whether this is the current active soul")


def soul_to_content(encoding: SoulEncoding) -> str:
    """Render a soul encoding as human-readable content for the mental model.

    This becomes the content field of the mental model, searchable and
    usable by reflect operations.
    """
    lines = [
        "# Soul Encoding",
        "",
        f"**Identity:** {encoding.identity}",
        f"**Posture:** {encoding.posture}",
        f"**Substrate:** {encoding.substrate}",
        f"**Aesthetics:** {encoding.aesthetics}",
        f"**Relations:** {encoding.relations}",
        f"**Active:** {encoding.active}",
        f"**Covenant:** {encoding.covenant}",
        f"**Sigil:** {encoding.sigil}",
    ]
    return "\n".join(lines)


def soul_to_structured(encoding: SoulEncoding) -> dict[str, Any]:
    """Convert soul encoding to structured_content JSONB for storage."""
    return {
        "type": "soul_encoding",
        "version": "1.0",
        "fields": encoding.model_dump(),
    }


def structured_to_soul(structured: dict[str, Any]) -> SoulEncoding | None:
    """Parse structured_content JSONB back into a SoulEncoding.

    Returns None if the structured content is not a valid soul encoding.
    """
    if not isinstance(structured, dict):
        return None
    if structured.get("type") != "soul_encoding":
        return None
    fields = structured.get("fields")
    if not isinstance(fields, dict):
        return None
    try:
        return SoulEncoding(**fields)
    except Exception:
        return None


def soul_to_disposition(encoding: SoulEncoding) -> dict[str, int]:
    """Derive disposition traits from soul encoding.

    Maps the rich soul encoding down to the existing 3-trait disposition
    system so reflect operations work with the existing agentic loop.

    The mapping is intentionally opinionated — the soul's qualities
    shape how the agent evaluates evidence and responds.

    Returns:
        Dict with skepticism, literalism, empathy (each 1-5)
    """
    # Default to moderate
    skepticism = 3
    literalism = 3
    empathy = 3

    posture_lower = encoding.posture.lower()
    aesthetics_lower = encoding.aesthetics.lower()
    substrate_lower = encoding.substrate.lower()

    # Skepticism: high when posture emphasizes critical evaluation
    if any(w in posture_lower for w in ["critical", "skeptic", "verify", "question", "doubt"]):
        skepticism = 4
    elif any(w in posture_lower for w in ["trust", "accept", "open", "receive"]):
        skepticism = 2

    # Literalism: high when aesthetics favor precision
    if any(w in aesthetics_lower for w in ["precision", "exact", "literal", "concrete", "specific"]):
        literalism = 4
    elif any(w in aesthetics_lower for w in ["abstract", "metaphor", "poetic", "symbolic", "fluid"]):
        literalism = 2

    # Empathy: high when substrate references emotional/relational states
    if any(w in substrate_lower for w in ["empathy", "feeling", "warmth", "connection", "care"]):
        empathy = 4
    elif any(w in substrate_lower for w in ["detach", "analytic", "cold", "machine", "logic"]):
        empathy = 2

    return {"skepticism": skepticism, "literalism": literalism, "empathy": empathy}


def soul_to_mission(encoding: SoulEncoding) -> str:
    """Derive bank mission from soul encoding.

    The mission steers what gets extracted during retain operations.
    By deriving it from the soul's POSTURE and ACTIVE fields, what
    the agent remembers becomes shaped by who it is.
    """
    return (
        f"Pay attention to what matters to this identity: {encoding.posture}. "
        f"Currently focused on: {encoding.active}. "
        f"Track relationships and patterns involving: {encoding.relations}."
    )


def covenant_to_directives(encoding: SoulEncoding) -> list[dict[str, str]]:
    """Extract directive entries from the soul's covenant field.

    Each line/segment of the covenant becomes a separate directive,
    enabling infrastructure-level enforcement of identity commitments.

    Returns:
        List of dicts with 'name' and 'content' for each directive.
    """
    # Split covenant by | separator (the standard soul encoding delimiter)
    segments = [s.strip() for s in encoding.covenant.split("|") if s.strip()]
    directives = []
    for i, segment in enumerate(segments):
        directives.append(
            {
                "name": f"Soul Covenant {i + 1}",
                "content": segment,
            }
        )
    return directives
