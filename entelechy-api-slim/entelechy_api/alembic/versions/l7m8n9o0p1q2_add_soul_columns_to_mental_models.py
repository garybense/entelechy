"""Add soul encoding columns to mental_models

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-06-05

Soul encodings are mental models with subtype='soul'. These columns track
version lineage (soul_version) and molt ancestry (soul_parent_id).
"""

from collections.abc import Sequence

from alembic import context, op

revision: str = "l7m8n9o0p1q2"
down_revision: str | Sequence[str] | None = "k6l7m8n9o0p1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_schema_prefix() -> str:
    schema = context.config.get_main_option("target_schema")
    return f'"{schema}".' if schema else ""


def upgrade() -> None:
    schema = _get_schema_prefix()

    op.execute(f"ALTER TABLE {schema}mental_models ADD COLUMN IF NOT EXISTS soul_version INTEGER")
    op.execute(f"ALTER TABLE {schema}mental_models ADD COLUMN IF NOT EXISTS soul_parent_id TEXT")

    op.execute(
        f"CREATE INDEX IF NOT EXISTS idx_mental_models_soul_lineage "
        f"ON {schema}mental_models (bank_id, subtype, soul_version DESC) "
        f"WHERE subtype = 'soul'"
    )

    op.execute(f"ALTER TABLE {schema}mental_models DROP CONSTRAINT IF EXISTS ck_mental_models_subtype")
    op.execute(f"""
        ALTER TABLE {schema}mental_models
        ADD CONSTRAINT ck_mental_models_subtype
        CHECK (subtype IN (
            'structural', 'emergent', 'pinned', 'learned', 'directive', 'soul'
        ))
    """)


def downgrade() -> None:
    schema = _get_schema_prefix()

    op.execute(f"DELETE FROM {schema}mental_models WHERE subtype = 'soul'")

    op.execute(f"DROP INDEX IF EXISTS {schema}idx_mental_models_soul_lineage")
    op.execute(f"ALTER TABLE {schema}mental_models DROP COLUMN IF EXISTS soul_parent_id")
    op.execute(f"ALTER TABLE {schema}mental_models DROP COLUMN IF EXISTS soul_version")

    op.execute(f"ALTER TABLE {schema}mental_models DROP CONSTRAINT IF EXISTS ck_mental_models_subtype")
    op.execute(f"""
        ALTER TABLE {schema}mental_models
        ADD CONSTRAINT ck_mental_models_subtype
        CHECK (subtype IN ('structural', 'emergent', 'pinned', 'learned', 'directive'))
    """)
