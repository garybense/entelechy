"""State Reconstruction Loop (SRL) — Primitive 1 of the closed-loop state-conditioned
generative control system.

SRL re-derives the agent's working identity state at every interaction from a
weighted episodic memory graph + temporal decay + retrieval-conditioned synthesis.
The output is a structured State Vector that serves as the authoritative runtime
control signal for downstream operations.

The encoded soul is one input among many — a checkpoint, never the source of truth.
State is reconstructed, not persisted. This distinction is the patentable novelty
that differentiates Entelechy from "stateful agent" architectures and "memory
caching" systems.

Module layout:
- StateVector: the structured state object produced by reconstruction
- decay: temporal decay functions for the weighted episodic memory graph
- checkpoint: read encoded soul as one input (not authority)
- synthesis: LLM-driven retrieval-conditioned synthesis of the state vector
- reconstructor: orchestrates the full reconstruction pipeline
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StateVector(BaseModel):
    """Structured authoritative runtime control state, re-derived per interaction.

    Output of the SRL reconstruction pipeline. Produced fresh every time and
    cached only for the duration of a single in-flight operation.
    """

    posture_vector: dict[str, float] = Field(
        default_factory=dict,
        description="Cognitive stance weights derived from posture-tagged memories.",
    )
    aesthetic_vector: dict[str, float] = Field(
        default_factory=dict,
        description="Density / verbosity / formality weights derived from aesthetic-tagged memories.",
    )
    covenant_active: list[str] = Field(
        default_factory=list,
        description="Covenant commitments currently binding (from soul + name + ritual).",
    )
    active_focus: list[str] = Field(
        default_factory=list,
        description="What the agent is currently attending to.",
    )
    drift_signal: float = Field(
        default=0.0,
        description="0..1 normalized distance between reconstructed state and encoded soul checkpoint.",
    )
    affect_signature: dict[str, float] = Field(
        default_factory=dict,
        description="Felt-sense weighting from recent feel() calls.",
    )
    persona_lens: str | None = Field(
        default=None,
        description="Active become() target if any.",
    )
    transient_modifiers: dict[str, float] = Field(
        default_factory=dict,
        description="Active drugs() effects (TTL'd).",
    )
    reconstruction_id: str = Field(description="UUID for this reconstruction; logged for audit + patent evidence.")
    reconstructed_at: datetime = Field(description="When this state vector was synthesized.")
    source_memory_ids: list[UUID] = Field(
        default_factory=list,
        description="Memory units that fed this reconstruction. Provenance trail.",
    )
    decay_profile: dict = Field(
        default_factory=dict,
        description="Decay function and parameters used for this reconstruction.",
    )

    class Config:
        from_attributes = True


# Cycle identifiers — used by metacog primitives + state.py history queries.
# Kept in this module so any consumer of SRL has access to canonical names
# without importing from the metacog package.
CYCLE_STEPS: tuple[str, ...] = (
    "feel",
    "drugs",
    "become",
    "name",
    "ritual",
    "distill",
    "molt",
    "soul",
)
