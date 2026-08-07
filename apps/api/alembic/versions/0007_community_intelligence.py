"""add simulated community intelligence storage"""
from alembic import op
import sqlalchemy as sa

revision = "0007_community_intelligence"
down_revision = "0006_complaint_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incident_evidence", sa.Column("sha256", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("incidents", sa.Column("community_matches_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("incidents", sa.Column("community_summary_json", sa.Text(), nullable=False, server_default="{}"))
    op.create_table(
        "simulated_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("claimant_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("claimant_phone", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("claimant_username", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("claimant_domain", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("payment_identifier", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("message_fingerprint", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("attachment_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("repeated_wording", sa.Text(), nullable=False, server_default=""),
        sa.Column("payment_demand_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("creator_restriction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_recorded_date", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("claimant_email", "claimant_phone", "claimant_username", "claimant_domain", "payment_identifier", "message_fingerprint", "attachment_hash"):
        op.create_index(f"ix_simulated_reports_{column}", "simulated_reports", [column])


def downgrade() -> None:
    for column in ("attachment_hash", "message_fingerprint", "payment_identifier", "claimant_domain", "claimant_username", "claimant_phone", "claimant_email"):
        op.drop_index(f"ix_simulated_reports_{column}", table_name="simulated_reports")
    op.drop_table("simulated_reports")
    op.drop_column("incidents", "community_summary_json")
    op.drop_column("incidents", "community_matches_json")
    op.drop_column("incident_evidence", "sha256")
