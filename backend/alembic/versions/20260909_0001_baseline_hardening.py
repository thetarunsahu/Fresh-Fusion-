"""Baseline FreshFusion hardening tables.

Revision ID: 20260909_0001
Revises:
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260909_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()

    # Fresh databases are created by SQLAlchemy metadata immediately after this
    # migration in the current prototype startup. Existing databases already
    # contain fruit_samples, so the additive tables below are created safely.
    if "fruit_samples" not in tables:
        return

    if "investigation_runs" not in tables:
        op.create_table(
            "investigation_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("sample_id", sa.String(length=32), sa.ForeignKey("fruit_samples.sample_id"), nullable=False),
            sa.Column("trigger", sa.String(length=40), nullable=True),
            sa.Column("snapshot", sa.JSON(), nullable=True),
            sa.Column("llm_explanation", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_investigation_runs_sample_id", "investigation_runs", ["sample_id"], unique=False)
        op.create_index("ix_investigation_runs_created_at", "investigation_runs", ["created_at"], unique=False)

    if "validation_runs" not in tables:
        op.create_table(
            "validation_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("run_id", sa.String(length=40), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=True),
            sa.Column("protocol", sa.String(length=80), nullable=True),
            sa.Column("sample_count", sa.Integer(), nullable=True),
            sa.Column("metrics", sa.JSON(), nullable=True),
            sa.Column("dataset_snapshot", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("run_id"),
        )
        op.create_index("ix_validation_runs_run_id", "validation_runs", ["run_id"], unique=True)
        op.create_index("ix_validation_runs_created_at", "validation_runs", ["created_at"], unique=False)

    if "model_versions" not in tables:
        op.create_table(
            "model_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("version", sa.String(length=80), nullable=False),
            sa.Column("artifact_path", sa.String(length=500), nullable=True),
            sa.Column("sha256", sa.String(length=64), nullable=True),
            sa.Column("labels", sa.JSON(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_model_versions_sha256", "model_versions", ["sha256"], unique=False)
        op.create_index("ix_model_versions_created_at", "model_versions", ["created_at"], unique=False)


def downgrade() -> None:
    tables = _tables()
    if "model_versions" in tables:
        op.drop_table("model_versions")
    if "validation_runs" in tables:
        op.drop_table("validation_runs")
    if "investigation_runs" in tables:
        op.drop_table("investigation_runs")
