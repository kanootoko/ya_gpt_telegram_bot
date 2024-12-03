# pylint: disable=no-member,invalid-name,missing-function-docstring,too-many-statements
"""add conversation table

Revision ID: 7b45cbd137c6
Revises: e2cac1279359
Create Date: 2024-11-30 18:45:17.806450

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b45cbd137c6"
down_revision: Union[str, None] = "e2cac1279359"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_from", sa.String(), autoincrement=False, nullable=False),
        sa.Column("user_to", sa.String(), autoincrement=False, nullable=True),
        sa.Column("message_timestamp", sa.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column("text", sa.String(), autoincrement=False, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conversation")
