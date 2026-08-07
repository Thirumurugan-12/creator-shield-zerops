"""create incident intake tables"""
from alembic import op
import sqlalchemy as sa

revision = "0004_incidents"
down_revision = "0003_processing_event_job"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("incidents", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("incident_id", sa.String(length=32), nullable=False), sa.Column("user_id", sa.String(length=64), nullable=False), sa.Column("proof_id", sa.Integer(), nullable=False), sa.Column("suspicious_storage_key", sa.String(length=500), nullable=False), sa.Column("suspicious_filename", sa.String(length=255), nullable=False), sa.Column("suspicious_file_size", sa.Integer(), nullable=False), sa.Column("suspicious_sha256", sa.String(length=64), nullable=False), sa.Column("suspicious_username", sa.String(length=120), nullable=False), sa.Column("claimed_publication_date", sa.String(length=32), nullable=False), sa.Column("suspicious_url", sa.String(length=500), nullable=False), sa.Column("caption", sa.Text(), nullable=False), sa.Column("notes", sa.Text(), nullable=False), sa.Column("status", sa.String(length=32), nullable=False), sa.Column("stage", sa.String(length=64), nullable=False), sa.Column("events_json", sa.Text(), nullable=False, server_default="[]"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["proof_id"], ["proofs.id"]), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_incidents_incident_id", "incidents", ["incident_id"], unique=True)
    op.create_index("ix_incidents_user_id", "incidents", ["user_id"], unique=False)
    op.create_index("ix_incidents_proof_id", "incidents", ["proof_id"], unique=False)
    op.create_index("ix_incidents_status", "incidents", ["status"], unique=False)
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"], unique=False)
    op.create_table("incident_evidence", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("incident_id", sa.Integer(), nullable=False), sa.Column("storage_key", sa.String(length=500), nullable=False), sa.Column("filename", sa.String(length=255), nullable=False), sa.Column("content_type", sa.String(length=120), nullable=False), sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_incident_evidence_incident_id", "incident_evidence", ["incident_id"], unique=False)

def downgrade() -> None:
    op.drop_table("incident_evidence")
    op.drop_table("incidents")
