# pylint: disable=no-member,invalid-name,missing-function-docstring,too-many-statements
"""Initial database state

Revision ID: e2cac1279359
Revises: 
Create Date: 2023-12-04 19:21:19.479907

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2cac1279359"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chats",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("AUTHORIZED", "PENDING", "UNAUTHORIZED", "BLOCKED", name="chat_status"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("added_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("chats_pk")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "SUPERADMIN",
                "ADMIN",
                "AUTHORIZED",
                "PENDING",
                "UNAUTHORIZED",
                "BLOCKED",
                "REVERSE_BLOCKED",
                name="user_status",
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("direct", sa.Boolean(), nullable=False),
        sa.Column("added_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("users_pk")),
    )

    op.create_table(
        "messages",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.BigInteger, nullable=False),
        sa.Column("reply_id", sa.BigInteger, nullable=True),
        sa.Column("from_self", sa.Boolean, nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("datetime", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], name=op.f("messages_fk_chat_id__chats")),
        sa.ForeignKeyConstraint(
            ["chat_id", "reply_id"], ["messages.chat_id", "messages.id"], name=op.f("messages_fk_reply_id__messages")
        ),
        sa.PrimaryKeyConstraint("chat_id", "id", name=op.f("messages_pk")),
    )

    op.create_table(
        "users_preferences",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("instruction_text", sa.String(length=1024), nullable=True),
        sa.Column("timeout", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("users_preferences_fk_user_id__users")),
        sa.PrimaryKeyConstraint("user_id", name=op.f("users_preferences_pk")),
    )


def downgrade() -> None:
    op.drop_table("users_preferences")
    op.drop_table("messages")
    op.drop_table("users")
    op.drop_table("chats")
