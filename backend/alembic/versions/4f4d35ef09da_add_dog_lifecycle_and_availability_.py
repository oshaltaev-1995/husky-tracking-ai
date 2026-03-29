"""add dog lifecycle and availability statuses

Revision ID: 4f4d35ef09da
Revises: c5ac0faecddd
Create Date: 2026-03-29 15:44:44.093955
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4f4d35ef09da"
down_revision = "c5ac0faecddd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "dogs",
        sa.Column(
            "lifecycle_status",
            sa.String(length=30),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "dogs",
        sa.Column(
            "availability_status",
            sa.String(length=30),
            nullable=False,
            server_default="available",
        ),
    )
    op.add_column(
        "dogs",
        sa.Column(
            "exclude_from_team_builder",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "dogs",
        sa.Column(
            "exclude_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # Optional cleanup: remove server defaults after existing rows are populated
    op.alter_column("dogs", "lifecycle_status", server_default=None)
    op.alter_column("dogs", "availability_status", server_default=None)
    op.alter_column("dogs", "exclude_from_team_builder", server_default=None)


def downgrade() -> None:
    op.drop_column("dogs", "exclude_reason")
    op.drop_column("dogs", "exclude_from_team_builder")
    op.drop_column("dogs", "availability_status")
    op.drop_column("dogs", "lifecycle_status")