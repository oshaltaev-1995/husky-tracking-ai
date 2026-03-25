"""align dogs table with static metadata

Revision ID: c5ac0faecddd
Revises: c60101667382
Create Date: 2026-03-25 18:58:11.870757
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c5ac0faecddd"
down_revision = "c60101667382"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dogs", sa.Column("external_id", sa.Integer(), nullable=True))
    op.add_column("dogs", sa.Column("kennel_block", sa.Integer(), nullable=True))
    op.add_column("dogs", sa.Column("primary_role", sa.String(length=50), nullable=True))

    op.add_column(
        "dogs",
        sa.Column(
            "can_lead",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "dogs",
        sa.Column(
            "can_team",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "dogs",
        sa.Column(
            "can_wheel",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.alter_column(
        "dogs",
        "home_slot",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="NULLIF(home_slot, '')::integer",
    )

    op.create_unique_constraint("uq_dogs_external_id", "dogs", ["external_id"])

    op.drop_column("dogs", "age_years")
    op.drop_column("dogs", "main_role")


def downgrade() -> None:
    op.add_column(
        "dogs",
        sa.Column("main_role", sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    )
    op.add_column(
        "dogs",
        sa.Column("age_years", sa.INTEGER(), autoincrement=False, nullable=True),
    )

    op.drop_constraint("uq_dogs_external_id", "dogs", type_="unique")

    op.alter_column(
        "dogs",
        "home_slot",
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(length=50),
        existing_nullable=True,
        postgresql_using="home_slot::text",
    )

    op.drop_column("dogs", "can_wheel")
    op.drop_column("dogs", "can_team")
    op.drop_column("dogs", "can_lead")
    op.drop_column("dogs", "primary_role")
    op.drop_column("dogs", "kennel_block")
    op.drop_column("dogs", "external_id")