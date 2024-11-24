"""Retrying middleware is defined here."""

import asyncio
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from loguru._logger import Logger

from ya_gpt_bot.ya_gpt import exceptions as ya_exc


def is_retryable(exc: Exception) -> bool:
    """Returns True if there is a sense in retrying the given exception cause."""
    if isinstance(exc, ya_exc.GenerationTimeoutError):  # network flaps
        return True
    if isinstance(exc, ya_exc.TextGenerationError) and exc.stasus == 500:  # model error
        return True
    return False


class RetryingMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """Retry certain exceptions given amount of times."""

    def __init__(self, max_retry_count: int):
        super().__init__()
        self.max_retry_count = max_retry_count

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        logger: Logger = data["logger"]
        for try_number in range(self.max_retry_count):
            try:
                await handler(event, data)
                break
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("event {} failed with following error: {!r}", data["event_id"], exc)
                if not is_retryable(exc):
                    logger.debug("Non-retryable error for event {}: {}", data["event_id"], type(exc))
                    raise
                if try_number < self.max_retry_count - 1:
                    logger.debug("Retry counts are finished for event {}", data["event_id"])
                    raise
                logger.debug("retrying event {} in 5 seconds", data["event_id"])
                asyncio.sleep(5)
