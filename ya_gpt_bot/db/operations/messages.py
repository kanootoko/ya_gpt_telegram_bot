"""Users common operations are defined here."""

from dataclasses import dataclass
from typing import Callable

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection

from ya_gpt_bot.db.entities import t_messages

func: Callable


@dataclass
class DialogEntry:
    """Dialog entry with indication whether the message was sent by the GPT bot."""

    message: str
    from_self: bool


async def save_message(  # pylint: disable=too-many-arguments
    conn: AsyncConnection,
    message_id: str,
    reply_id: str | None,
    chat_id: str,
    text: str,
    from_self: bool,
) -> None:
    """Save message (from user talking with GPT or model responsing to user)."""
    try:
        await conn.execute(
            insert(t_messages).values(id=message_id, reply_id=reply_id, chat_id=chat_id, text=text, from_self=from_self)
        )
    except IntegrityError:
        await conn.rollback()
        await conn.execute(insert(t_messages).values(id=message_id, chat_id=chat_id, text=text, from_self=from_self))

    await conn.commit()


async def get_dialog(conn: AsyncConnection, chat_id: int, reply_id: str) -> list[DialogEntry]:
    """Return dialog starting with user"""
    statement = select(
        t_messages.c.chat_id,
        t_messages.c.id,
        t_messages.c.reply_id,
        t_messages.c.text,
        t_messages.c.from_self,
        t_messages.c.datetime,
    )
    cte_statement = statement.where(t_messages.c.chat_id == chat_id, t_messages.c.id == reply_id).cte(
        name="messages_recursive", recursive=True
    )

    recursive_part = statement.join(
        cte_statement, (t_messages.c.chat_id == cte_statement.c.chat_id) & (t_messages.c.id == cte_statement.c.reply_id)
    )

    statement = select(cte_statement.union_all(recursive_part)).order_by(cte_statement.c.datetime)

    dialog = [DialogEntry(entry[3], entry[4]) for entry in await conn.execute(statement)]
    return dialog
