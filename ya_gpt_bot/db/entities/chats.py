"""Chats database table is defined here."""
from typing import Callable

from sqlalchemy import TIMESTAMP, BigInteger, Column, Enum, Table, func

from ya_gpt_bot.db.metadata import metadata

from .enums import ChatStatus, UserStatus

func: Callable

t_chats = Table(
    "chats",
    metadata,
    Column("id", BigInteger, primary_key=True, nullable=False),
    Column("status", Enum(ChatStatus, name="chat_status"), nullable=False, server_default=UserStatus.PENDING.value),
    Column("added_at", TIMESTAMP(True), nullable=False, server_default=func.now()),
    Column("updated_at", TIMESTAMP(True), nullable=False, server_default=func.now()),
)
"""Chats that have added the bot.

Columns:
- `id` - user identifier, big integer
- `status` - user status, UserStatus enum
- `direct` - indicates whether the user contacted the bot directly, boolean
- `added_at` - time of first interraction with chat, timestamptz
- `updated_at` - time of last status change for user, timestamptz
"""
