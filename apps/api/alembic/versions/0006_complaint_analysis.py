"""add complaint extraction and suspicion analysis fields"""
from alembic import op
import sqlalchemy as sa

revision = "0006_complaint_analysis"
down_revision = "0005_comparison_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("complaint_extraction_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("incidents", sa.Column("suspicion_score", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("suspicion_band", sa.String(length=32), nullable=True))
    op.add_column("incidents", sa.Column("suspicion_indicators_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("incidents", "suspicion_indicators_json")
    op.drop_column("incidents", "suspicion_band")
    op.drop_column("incidents", "suspicion_score")
    op.drop_column("incidents", "complaint_extraction_json")
