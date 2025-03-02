"""Service to get and update conversations."""

import datetime
from textwrap import dedent
from typing import Callable

from aiogram.types import Message
from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from ya_gpt_bot.db.entities.conversation import t_conversation

func: Callable


DEFAULT_INSTRUCTION_PROMPT = dedent(
    """
    Следующим блоком будут переданы сообщения из чата, написанные разными людьми.
    Проанализируй сообщения и создай краткое содержание беседы, выразив суть обсуждаемого и позиции участников.

    Формат текста - в каждой строке лога содержатся следующие колонки, разделенные запятой:
        - ник отправителя
        - ник получателя
        - текст сообщения.
    Основываясь на этих данных, определи тему обсуждения, сформулируй позиции участников.
    Обязательно укажи их никнеймы в ответе, не используй обезличенные слова.
    Ответ представь в виде связного текста, где будет отражена динамика диалога и ключевые моменты дискуссии.
    Не начинай ответ со слов "в данном фрагменте/тексте/чате", сразу начинай с описания.
    В качестве символов разделителей списка, если они понадобятся, используй "-".

    Если в тексте сообщений поднимаются темы, которые нельзя обсуждать, просто игнорируй такие сообщения полностью, их суммаризировать не нужно.
    """  # pylint: disable=line-too-long
)


class ConversationService:
    """Service to get and update conversations."""

    def __init__(self, engine: AsyncEngine, instruction_prompt: str = ...):
        """Initialize ConversationService with database engine and optional instruction."""
        self._engine = engine
        if instruction_prompt is ...:
            instruction_prompt = DEFAULT_INSTRUCTION_PROMPT
        self._instruction_prompt = instruction_prompt

    def get_instruction_prompt(self) -> str:
        """Return instructions for a GPT service."""
        return self._instruction_prompt

    async def get_chat_messages_history(self, chat_id: int, context_length: int) -> str:
        """Return combined messages."""
        messages = await self._get_messages_within_context(chat_id, context_length - len(self._instruction_prompt) - 1)
        if not messages:
            return ""

        messages_joined = "\n".join(messages)
        return messages_joined

    async def _get_messages_within_context(self, chat_id: int, all_messages_length: int) -> list[str]:
        """Return messages withing defined context from the chat and clear messages that are out of context."""
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

    async def save_message(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, chat_id: int, from_name: str, to_name: str, message_timestamp: datetime.datetime, text: str
    ):
        """Save messages to conversation table."""
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

    # TODO: implement
    def saving_text(self, message: Message) -> str | None:  # pylint: disable=unused-argument
        """Check if user wants to save their messages for the digest."""
        if message.chat.type == "private":
            return None
        text = message.text
        if message.caption is not None:
            text = f"(Изображение) {message.caption}"
        if text is None or text == "":
            return None
        return text
