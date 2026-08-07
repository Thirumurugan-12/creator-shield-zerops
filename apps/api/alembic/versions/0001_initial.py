"""create core CreatorShield persistence tables"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.String(length=64), primary_key=True), sa.Column("display_name", sa.String(length=120), nullable=False), sa.Column("instagram_username", sa.String(length=120), nullable=False), sa.Column("email", sa.String(length=255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_users_instagram_username", "users", ["instagram_username"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("proofs", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("proof_id", sa.String(length=32), nullable=False), sa.Column("user_id", sa.String(length=64), nullable=False), sa.Column("title", sa.String(length=240), nullable=False), sa.Column("instagram_username", sa.String(length=120), nullable=False), sa.Column("claimed_publication_date", sa.String(length=32), nullable=False), sa.Column("claimed_publication_url", sa.String(length=500), nullable=False), sa.Column("caption", sa.Text(), nullable=False), sa.Column("notes", sa.Text(), nullable=False), sa.Column("original_filename", sa.String(length=255), nullable=False), sa.Column("storage_key", sa.String(length=500), nullable=False), sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("sha256", sa.String(length=64), nullable=False), sa.Column("status", sa.String(length=32), nullable=False), sa.Column("current_step", sa.String(length=64), nullable=False), sa.Column("progress", sa.Integer(), nullable=False), sa.Column("evidence_completeness", sa.Integer(), nullable=False), sa.Column("duration", sa.Float(), nullable=True), sa.Column("width", sa.Integer(), nullable=True), sa.Column("height", sa.Integer(), nullable=True), sa.Column("transcript", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_proofs_proof_id", "proofs", ["proof_id"], unique=True)
    op.create_index("ix_proofs_user_id", "proofs", ["user_id"], unique=False)
    op.create_index("ix_proofs_sha256", "proofs", ["sha256"], unique=False)
    op.create_index("ix_proofs_status", "proofs", ["status"], unique=False)
    op.create_index("ix_proofs_created_at", "proofs", ["created_at"], unique=False)
    op.create_table("processing_jobs", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("proof_id", sa.Integer(), nullable=False), sa.Column("status", sa.String(length=32), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False), sa.Column("error_message", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["proof_id"], ["proofs.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_processing_jobs_proof_id", "processing_jobs", ["proof_id"], unique=False)
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"], unique=False)
    op.create_table("processing_events", sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("proof_id", sa.Integer(), nullable=False), sa.Column("message", sa.String(length=500), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["proof_id"], ["proofs.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_processing_events_proof_id", "processing_events", ["proof_id"], unique=False)
    op.create_index("ix_processing_events_created_at", "processing_events", ["created_at"], unique=False)

def downgrade() -> None:
    op.drop_table("processing_events")
    op.drop_table("processing_jobs")
    op.drop_table("proofs")
    op.drop_table("users")
