# pylint: disable=no-member,invalid-name,missing-function-docstring,too-many-statements
"""Increase instuction_text, add ignore_quote

Revision ID: 3db8b444adaa
Revises: 7b45cbd137c6
Create Date: 2026-08-22 09:53:22.745854

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3db8b444adaa"
down_revision: Union[str, None] = "7b45cbd137c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users_preferences", "instruction_text", type_=sa.String(4096))
    op.add_column(
        "users_preferences",
        sa.Column(
            "ignore_quote",
            sa.Boolean(),
            nullable=False,
            server_default=sa.False_(),
        ),
    )
    op.add_column(
        "messages",
        sa.Column("system_text", sa.String(), nullable=True, server_default=sa.null()),
    )


def downgrade() -> None:
    op.drop_column("messages", "system_text")
    op.drop_column("user_preferences", "ignore_quote")
    op.alter_column("users_preferences", "instruction_text", type_=sa.String(1024))
