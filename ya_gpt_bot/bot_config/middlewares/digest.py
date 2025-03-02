"""Digest history saving middleware is defined here."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from loguru._logger import Logger

from ya_gpt_bot.services.impl.conversation_service import ConversationService


class DigestHistorySavingMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """Log every user action as info, exception tracebacks as debug."""

    def __init__(self, conversation_service: ConversationService):
        self._conversation_service = conversation_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        """Save every message (except users who opted-out) for the later digest."""
        logger: Logger = data["logger"]
        if isinstance(event, Message):
            try:
                await self._handle_saving(event)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Could not save message for a digest: {!r}", exc)
        return await handler(event, data)

    async def _handle_saving(self, message: Message) -> None:
        to_name = None if message.reply_to_message is None else message.reply_to_message.from_user.username
        text = self._conversation_service.saving_text(message)
        if text is None:
            return
        await self._conversation_service.save_message(
            chat_id=message.chat.id,
            from_name=message.from_user.username,
            to_name=to_name,
            message_timestamp=message.date,
            text=text,
        )
