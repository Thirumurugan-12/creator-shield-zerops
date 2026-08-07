"""link processing events to jobs"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_processing_event_job"
down_revision = "0002_processing_artifacts"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("processing_events")}
    if "job_id" not in columns:
        with op.batch_alter_table("processing_events", recreate="always") as batch:
            batch.add_column(sa.Column("job_id", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_processing_events_job_id", "processing_jobs", ["job_id"], ["id"])
    indexes = {index["name"] for index in inspect(bind).get_indexes("processing_events")}
    if "ix_processing_events_job_id" not in indexes:
        op.create_index("ix_processing_events_job_id", "processing_events", ["job_id"], unique=False)

def downgrade() -> None:
    with op.batch_alter_table("processing_events", recreate="always") as batch:
        batch.drop_constraint("fk_processing_events_job_id", type_="foreignkey")
        batch.drop_index("ix_processing_events_job_id")
        batch.drop_column("job_id")
