"""Logging middleware is defined here."""

import time
import traceback
import uuid
from typing import Any, Awaitable, Callable, Literal

from aiogram import BaseMiddleware
from aiogram.types import Message, ReactionTypeEmoji, TelegramObject
from loguru._logger import Logger

from ya_gpt_bot.bot_config.texts import get_responses
from ya_gpt_bot.services.messages_service import MessagesService
from ya_gpt_bot.ya_gpt.exceptions import GPTInvalidPrompt


def _user_from_event(event: TelegramObject, log: Logger) -> str:
    if hasattr(event, "from_user"):
        if hasattr(event.from_user, "id"):
            return event.from_user.id
    log.debug("Cannot get user from event: {}", event)
    return "<unknown>"


_responses = get_responses()


class LoggingMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """Log every user action as info, exception tracebacks as debug."""

    def __init__(self, logger: Logger, verbosity_level: Literal[0, 1, 2] = 1):
        """Verbosity level options:

        0: no reaction from bot on error
        1: sad reaction is set on user message
        2: template text is sent back
        3: error repr is sent back
        """
        self._logger = logger
        self._verbosity_level = verbosity_level

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        """Middleware call."""
        event_id = str(uuid.uuid4())
        data["event_id"] = event_id
        logger = self._logger.bind(event_id=event_id)
        data["logger"] = logger

        messages_service: MessagesService = data["messages_service"]

        logger.info("User {} initiated event '{}'", _user_from_event(event, logger), type(event).__name__)
        start_time = time.time()
        try:
            result = await handler(event, data)
            return result
        except GPTInvalidPrompt:
            if isinstance(event, Message):
                message = await event.reply(_responses.invalid_prompt_error)
                await messages_service.save_message(
                    message.message_id, event.message_id, event.chat.id, _responses.invalid_prompt_error, True
                )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Exception '{!r}' on processing event {}", exc, event_id)
            logger.debug("Traceback: {}", traceback.format_exc())
            if isinstance(event, Message):
                if self._verbosity_level == 1:
                    await event.react([ReactionTypeEmoji(emoji="😢")])
                elif self._verbosity_level == 2:
                    await event.reply("Error occured on request handling")
                elif self._verbosity_level == 3:
                    await event.reply("Error occured on request handling: {!r}", exc)
            raise
        finally:
            logger.info("Event finished in {:.3f} seconds", time.time() - start_time)
