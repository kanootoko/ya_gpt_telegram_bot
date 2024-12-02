"""Requests database table is defined here."""

from sqlalchemy import TIMESTAMP, BigInteger, Column, String, Table

from ya_gpt_bot.db.metadata import metadata

t_conversation = Table(
    "conversation",
    metadata,
    Column("chat_id", BigInteger(), nullable=False),
    Column("user_from", String(), autoincrement=False, nullable=False),
    Column("user_to", String(), autoincrement=False, nullable=True),
    Column("message_timestamp", TIMESTAMP(timezone=False), autoincrement=False, nullable=True),
    Column("text", String(), autoincrement=False, nullable=False),
)
"""
Messages logging table for full conversation - purely for digest function

Columns:
- `chat_id` - identifier of a chat if the request was sent from chat, big integer nullable
- `user_from` - message sender name
- `user_to` - message reciever name
- `message_timestamp` - time of a message sent
- `text` - text of a message, string
"""
