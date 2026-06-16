"""add_teams_and_task_assignment

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-16 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teams_id"), "teams", ["id"], unique=False)

    # 2. Create team_members table
    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "owner",
                "admin",
                "member",
                name="teamrole",
                native_enum=False,
                length=50,
            ),
            nullable=False,
            server_default="member",
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )
    op.create_index(
        op.f("ix_team_members_id"), "team_members", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_team_members_team_id"),
        "team_members",
        ["team_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_team_members_user_id"),
        "team_members",
        ["user_id"],
        unique=False,
    )

    # 3. Add assignee_id to tasks table
    op.add_column("tasks", sa.Column("assignee_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_assignee_id",
        "tasks",
        "users",
        ["assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False
    )


def downgrade() -> None:
    # 1. Remove assignee_id from tasks
    op.drop_index(op.f("ix_tasks_assignee_id"), table_name="tasks")
    op.drop_constraint("fk_tasks_assignee_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "assignee_id")

    # 2. Drop team_members table
    op.drop_index(op.f("ix_team_members_user_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_team_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_id"), table_name="team_members")
    op.drop_table("team_members")

    # 3. Drop teams table
    op.drop_index(op.f("ix_teams_id"), table_name="teams")
    op.drop_table("teams")
