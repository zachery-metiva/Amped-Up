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
    # Use raw DDL so Postgres doesn't try to CREATE TYPE for enums that already exist
    op.execute("""
        CREATE TABLE predicted_reports (
            id VARCHAR(64) NOT NULL PRIMARY KEY,
            pole_id VARCHAR(64) NOT NULL REFERENCES poles(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            predicted_severity severity NOT NULL,
            risk_score DOUBLE PRECISION NOT NULL,
            risk_factors JSONB,
            status report_status NOT NULL,
            generated_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
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
