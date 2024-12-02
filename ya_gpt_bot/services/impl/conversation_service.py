"""Service to get and update conversations."""
import datetime

from sqlalchemy import insert
from sqlalchemy import text as sa_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from ya_gpt_bot.db.entities.conversation import t_conversation

AGG_CTE = """
    with agg as (
        select
            user_from || ',' || coalesce(user_to, '') || ',' || text as full_message,
            message_timestamp as ts
        from
            ya_gpt_bot.public.conversation c
        where
            chat_id = :chat_id
    )
"""

EXTRACT_QUERY = sa_text(
    AGG_CTE
    + """
    , windowed as (
        select
            full_message,
            ts,
            sum(length(full_message)) over (order by ts desc) < :context_size as fit_in_context
        from agg
        order by ts
    )
    select full_message
    from windowed
    where fit_in_context
"""
)

# Query to delete messages not fitting in the context
DELETE_QUERY = sa_text(
    AGG_CTE
    + """
    , windowed as (
        select
            ts,
            sum(length(full_message)) over (order by ts desc) < :context_size as fit_in_context
        from agg
        order by ts
    )
    delete from ya_gpt_bot.public.conversation
    where message_timestamp in (
        select ts from windowed where not fit_in_context
    )
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
            messages_in_context = await conn.execute(
                EXTRACT_QUERY, {"context_size": context_length, "chat_id": chat_id}
            )

            await conn.execute(DELETE_QUERY, {"context_size": context_length, "chat_id": chat_id})
            await conn.commit()
            return [m[0] for m in messages_in_context.fetchall()]

    async def save_message(  # pylint: disable=too-many-arguments
        self, chat_id: int, from_name: str, to_name: str, message_timestamp: datetime.datetime, text: str
    ):
        """save messages to conversation table"""
        async with self.__engine.connect() as conn:
            try:
                await conn.execute(
                    insert(t_conversation).values(
                        chat_id=chat_id,
                        user_from=from_name,
                        user_to=to_name,
                        message_timestamp=message_timestamp,
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
                        message_timestamp=message_timestamp,
                        text=text,
                    )
                )

            await conn.commit()
