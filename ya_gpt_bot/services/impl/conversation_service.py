"""Service to get and update conversations."""
import datetime
from textwrap import dedent
from typing import Callable

from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from ya_gpt_bot.db.entities.conversation import t_conversation

func: Callable


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
            agg_cte = (
                select(
                    (
                        func.length(t_conversation.c.user_from)
                        + 1
                        + func.length(func.coalesce(t_conversation.c.user_to, ""))
                        + 1
                        + func.length(t_conversation.c.text)
                        + 1
                    ).label("full_message_length"),
                    t_conversation.c.message_timestamp.label("ts"),
                )
                .where(t_conversation.c.chat_id == chat_id)
                .cte("agg")
            )

            windowed_cte = select(
                agg_cte.c.ts,
                (
                    func.sum(agg_cte.c.full_message_length).over(order_by=agg_cte.c.ts.desc()) < all_messages_length
                ).label("fit_in_context"),
            ).cte("windowed")

            result = (
                await conn.execute(
                    select(func.min(windowed_cte.c.ts).label("min_ts")).where(windowed_cte.c.fit_in_context)
                )
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

    def should_save(self, chat_id: int, user_id: int) -> bool:  # pylint: disable=unused-argument
        """TODO: check if user wants to save his messages for the digest"""
        return True
