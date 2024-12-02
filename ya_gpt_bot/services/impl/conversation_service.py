"""Service to get and update conversations."""
import datetime
from typing import Callable

from sqlalchemy import delete, func, insert, select
from sqlalchemy import text as sa_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from ya_gpt_bot.db.entities.conversation import t_conversation

func: Callable

MIN_TS_SQL = sa_text(
    """
with agg as (
    select
        user_from || ',' || coalesce(user_to, '') || ',' || text as full_message,
        message_timestamp as ts
    from
        ya_gpt_bot.public.conversation c
    where
        chat_id = :chat_id
),
windowed as (
    select
        ts,
        sum(length(full_message) + 1) over (order by ts desc) < :context_size as fit_in_context
    from
        agg
)
select min(ts) as min_ts
from windowed
where fit_in_context;
"""
)


class ConversationService:
    """Service to get and update conversations."""

    def __init__(self, engine: AsyncEngine):
        """init"""
        self.__engine = engine

    async def get_messages_within_context(self, chat_id: int, context_length: int) -> list[str]:
        """get messages withing defined context from the chat and clear messages that are out of context"""
        async with self.__engine.connect() as conn:
            result = (await conn.execute(MIN_TS_SQL, {"context_size": context_length, "chat_id": chat_id})).fetchone()
            min_ts = result[0].replace(tzinfo=None) if result else None

            if min_ts:
                full_message_expr = func.concat(
                    t_conversation.c.user_from,
                    ",",
                    func.coalesce(t_conversation.c.user_to, ""),
                    ",",
                    t_conversation.c.text,
                ).label("full_message")
                select_results = await conn.execute(
                    select(full_message_expr)
                    .where(t_conversation.c.message_timestamp >= min_ts, t_conversation.c.chat_id == chat_id)
                    .order_by(t_conversation.c.message_timestamp)
                )
                await conn.execute(
                    delete(t_conversation).where(
                        t_conversation.c.message_timestamp < min_ts, t_conversation.c.chat_id == chat_id
                    )
                )
                await conn.commit()
                return [m[0] for m in select_results.fetchall()]

    async def save_message(  # pylint: disable=too-many-arguments
        self, chat_id: int, from_name: str, to_name: str, message_timestamp: datetime.datetime, text: str
    ):
        """save messages to conversation table"""
        no_tz = message_timestamp.replace(tzinfo=None)
        async with self.__engine.connect() as conn:
            try:
                await conn.execute(
                    insert(t_conversation).values(
                        chat_id=chat_id,
                        user_from=from_name,
                        user_to=to_name,
                        message_timestamp=no_tz,
                        text=text,
                    )
                )
            except IntegrityError:
                await conn.rollback()
                await conn.execute(
                    insert(t_conversation).values(
                        chat_id=chat_id,
                        user_from=from_name,
                        user_to=to_name,
                        message_timestamp=no_tz,
                        text=text,
                    )
                )

            await conn.commit()
