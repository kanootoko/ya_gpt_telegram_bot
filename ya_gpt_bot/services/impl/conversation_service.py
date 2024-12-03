"""Service to get and update conversations."""
import datetime
from textwrap import dedent
from typing import Callable

from sqlalchemy import delete, func, insert, select
from sqlalchemy import text as sa_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from ya_gpt_bot.db.entities.conversation import t_conversation

func: Callable

MIN_TS_SQL = sa_text(
    dedent(
        # colon, colon and line break
        """
        with agg as (
            select
                length(user_from) + 1 + length(coalesce(user_to, '')) + 1 + length(text) + 1 as full_message_length,
                message_timestamp as ts
            from
                ya_gpt_bot.public.conversation c
            where
                chat_id = :chat_id
        ),
        windowed as (
            select
                ts,
                sum(full_message_length) over (order by ts desc) < :context_size as fit_in_context
            from
                agg
        )
        select min(ts) as min_ts
        from windowed
        where fit_in_context;
        """
    )
)

# around 150 symbols
PROMPT_INIT = (
    "Сделай выжимку происходившего в чате используя "
    "сsv лог с тремя колонками: от кого, кому, текст сообщения. "
    "Сообщения идут в хронологическом порядке."
)


class ConversationService:
    """Service to get and update conversations."""

    def __init__(self, engine: AsyncEngine):
        """init"""
        self._engine = engine

    async def get_prompt(self, chat_id: int, context_length: int) -> str:
        """get full prompt with pre-prompt substituted"""
        messages = await self._get_messages_within_context(chat_id, context_length - len(PROMPT_INIT) - 1)
        if not messages:
            return ""
        messages_joined = "\n".join(messages)
        return dedent(
            f"""
            {PROMPT_INIT}
            {messages_joined}
            """
        )

    async def _get_messages_within_context(self, chat_id: int, all_messages_length: int) -> list[str]:
        """get messages withing defined context from the chat and clear messages that are out of context"""
        async with self._engine.connect() as conn:
            result = (
                await conn.execute(MIN_TS_SQL, {"context_size": all_messages_length, "chat_id": chat_id})
            ).fetchone()
            min_ts = result[0] if result else None

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
        no_tz = message_timestamp
        async with self._engine.connect() as conn:
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
