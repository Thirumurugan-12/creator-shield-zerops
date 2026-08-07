"""add incident comparison result fields"""
from alembic import op
import sqlalchemy as sa

revision = "0005_comparison_results"
down_revision = "0004_incidents"
branch_labels = None
depends_on = None

def upgrade() -> None:
    for name, column in [("visual_similarity", sa.Float()), ("audio_similarity", sa.Float()), ("transcript_similarity", sa.Float()), ("timeline_confidence", sa.Float()), ("combined_similarity", sa.Float()), ("matching_segments", sa.Integer()), ("matching_audio_seconds", sa.Float())]:
        op.add_column("incidents", sa.Column(name, column, nullable=True))
    op.add_column("incidents", sa.Column("modifications_json", sa.Text(), nullable=False, server_default="[]"))

def downgrade() -> None:
    op.drop_column("incidents", "modifications_json")
    for name in ["matching_audio_seconds", "matching_segments", "combined_similarity", "timeline_confidence", "transcript_similarity", "audio_similarity", "visual_similarity"]:
        op.drop_column("incidents", name)
