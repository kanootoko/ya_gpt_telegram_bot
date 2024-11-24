"""Users database table is defined here."""

from typing import Callable

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, Enum, Table, func

from ya_gpt_bot.db.metadata import metadata

from .enums import UserStatus

func: Callable

t_users = Table(
    "users",
    metadata,
    Column("id", BigInteger, primary_key=True, nullable=False),
    Column("status", Enum(UserStatus, name="user_status"), nullable=False, server_default=UserStatus.PENDING.value),
    Column("direct", Boolean, nullable=False),
    Column("added_at", TIMESTAMP(True), nullable=False, server_default=func.now()),
    Column("updated_at", TIMESTAMP(True), nullable=False, server_default=func.now()),
)
"""Users that sent messages to the bot (directly or from a chat).

Columns:
- `id` - user identifier, big integer
- `status` - user status, UserStatus enum
- `direct` - indicates whether the user contacted the bot directly, boolean
- `added_at` - time of first interraction with user, timestamptz
- `updated_at` - time of last status change for user, timestamptz
"""
