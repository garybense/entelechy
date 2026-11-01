"""Add policy_history table

Revision ID: m8n9o0p1q2r3
Revises: l7m8n9o0p1q2
Create Date: 2026-11-01

Stores every policy (Vector P) computed for a bank together with the Vector F and
state vector it was derived from. The latest row is the previous policy that
policy inertia clamps the next one against.
"""

from collections.abc import Sequence

from alembic import context, op

revision: str = "m8n9o0p1q2r3"
down_revision: str | Sequence[str] | None = "l7m8n9o0p1q2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_schema_prefix() -> str:
    schema = context.config.get_main_option("target_schema")
    return f'"{schema}".' if schema else ""


def upgrade() -> None:
    schema = _get_schema_prefix()
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {schema}policy_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            bank_id TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            policy JSONB NOT NULL,
            rationale TEXT,
            vector_f JSONB,
            state_vector JSONB,
            inertia_applied BOOLEAN NOT NULL DEFAULT FALSE
        )
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS idx_policy_history_bank_created ON {schema}policy_history (bank_id, created_at DESC)"
    )


def downgrade() -> None:
    schema = _get_schema_prefix()
    op.execute(f"DROP INDEX IF EXISTS {schema}idx_policy_history_bank_created")
    op.execute(f"DROP TABLE IF EXISTS {schema}policy_history")
