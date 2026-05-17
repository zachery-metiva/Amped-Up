"""create predicted reports table

Revision ID: 3a4c9b7d1e2f
Revises: cb6102218faa
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3a4c9b7d1e2f"
down_revision: Union[str, None] = "cb6102218faa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "predicted_reports",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("pole_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("predicted_severity", sa.Enum("critical", "high", "medium", "low", name="severity", create_type=False), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_factors", sa.JSON(), nullable=True),
        sa.Column("status", sa.Enum("open", "snoozed", "approved", "dismissed", name="report_status", create_type=False), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["pole_id"], ["poles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_predicted_reports_generated_at"), "predicted_reports", ["generated_at"], unique=False)
    op.create_index(op.f("ix_predicted_reports_pole_id"), "predicted_reports", ["pole_id"], unique=False)
    op.create_index(op.f("ix_predicted_reports_predicted_severity"), "predicted_reports", ["predicted_severity"], unique=False)
    op.create_index(op.f("ix_predicted_reports_risk_score"), "predicted_reports", ["risk_score"], unique=False)
    op.create_index(op.f("ix_predicted_reports_status"), "predicted_reports", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_predicted_reports_status"), table_name="predicted_reports")
    op.drop_index(op.f("ix_predicted_reports_risk_score"), table_name="predicted_reports")
    op.drop_index(op.f("ix_predicted_reports_predicted_severity"), table_name="predicted_reports")
    op.drop_index(op.f("ix_predicted_reports_pole_id"), table_name="predicted_reports")
    op.drop_index(op.f("ix_predicted_reports_generated_at"), table_name="predicted_reports")
    op.drop_table("predicted_reports")
