"""add tool category and tags

Revision ID: 002
Revises: 001
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tools", sa.Column("category", sa.String(100), nullable=True))
    op.add_column("tools", sa.Column("tags", sa.JSON, nullable=True, server_default="[]"))
    op.create_index("idx_tools_category", "tools", ["category"], postgresql_where=sa.text("category IS NOT NULL"))

    # Form submissions table
    op.create_table(
        "form_submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tool_id", sa.String(36), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("submitted_by", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_form_submissions_tool_id", "form_submissions", ["tool_id"])
    op.create_index("idx_form_submissions_created_at", "form_submissions", [sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("form_submissions")
    op.drop_index("idx_tools_category", table_name="tools")
    op.drop_column("tools", "tags")
    op.drop_column("tools", "category")
