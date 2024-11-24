"""Requests database table is defined here."""

from typing import Callable

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, ForeignKeyConstraint, String, Table, func

from ya_gpt_bot.db.metadata import metadata

func: Callable

t_messages = Table(
    "messages",
    metadata,
    # not ForeignKey("chats.id") because direct messages chats are not dumped to chats table
    Column("chat_id", BigInteger, primary_key=True, nullable=False),
    Column("id", BigInteger, primary_key=True, nullable=False),
    Column("reply_id", BigInteger),
    Column("from_self", Boolean, nullable=False),
    Column("text", String, nullable=False),
    Column("datetime", TIMESTAMP(True), nullable=False, server_default=func.now()),
    ForeignKeyConstraint(["chat_id", "reply_id"], ["messages.chat_id", "messages.id"]),
)
"""Messages logging table

Columns:
- `chat_id` - identifier of a chat if the request was sent from chat, big integer nullable
- `id` - request identifier, integer
- `reply_id` - identifier of a message which this message replies, big integer, optional
- `user_id` - identifier of a concrete user who created a request, big integer
- `text` - text of request, varchar
- `datetime` - time of request finish, timestamptz
"""
