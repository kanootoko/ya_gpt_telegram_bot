"""Fallback router which will answer with soft error in case no other router was executed is defined here."""

from aiogram import Router
from aiogram.types import Message
from loguru import logger as global_logger
from loguru._logger import Logger

from ya_gpt_bot.bot_config.filters import DirectMessage
from ya_gpt_bot.bot_config.texts import get_responses

responses = get_responses()

fallback_router = Router(name="direct_messages_router")

fallback_router.message()
fallback_router.message.filter(DirectMessage())


@fallback_router.message()
async def fallback_return_response(message: Message, text: str | None = None, logger: Logger = global_logger) -> None:
    """Respond with error of no handlers available"""
    if text == "":
        return
    logger.warning("Could not handle following message (using fallback): {}", message)
    await message.reply(responses.no_handler_available)
