"""add media processing artifact fields"""
from alembic import op
import sqlalchemy as sa

revision = "0002_processing_artifacts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("proofs", sa.Column("codec", sa.String(length=64), nullable=True))
    op.add_column("proofs", sa.Column("frame_rate", sa.Float(), nullable=True))
    op.add_column("proofs", sa.Column("audio_present", sa.Boolean(), nullable=True))
    op.add_column("proofs", sa.Column("audio_fingerprint", sa.String(length=128), nullable=True))
    op.add_column("proofs", sa.Column("keyframes_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("proofs", sa.Column("transcript_status", sa.String(length=32), nullable=False, server_default="unavailable"))

def downgrade() -> None:
    op.drop_column("proofs", "transcript_status")
    op.drop_column("proofs", "keyframes_json")
    op.drop_column("proofs", "audio_fingerprint")
    op.drop_column("proofs", "audio_present")
    op.drop_column("proofs", "frame_rate")
    op.drop_column("proofs", "codec")
