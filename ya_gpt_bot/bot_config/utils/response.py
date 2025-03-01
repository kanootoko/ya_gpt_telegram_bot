"""Response utilities are defined here."""

import aiogram
import aiogram.exceptions
from aiogram.enums import ParseMode
from aiogram.types import Message
from loguru import logger


def split_to_multiple_messages(text: str) -> list[str]:
    """Split long message to a multiple messages each having maximum length below 1024."""
    texts: list[str] = []
    while len(text) > 1024:
        split_index = text[:1024].rfind("\n")
        if split_index == -1:
            split_index = text[:1024].rfind(" ")
            if split_index == -1:
                split_index = 1024
        texts.append(text[:split_index])
        text = text[split_index + 1 :]
    texts.append(text)
    return texts


async def reply_with_html_fallback(message: Message, text: str) -> list[Message]:
    """Reply with a default parse_mode for client, on TelegramBadRequest error retry with HTML"""
    texts = split_to_multiple_messages(text)
    messages: list[Message] = []
    for sending_text in texts:
        try:
            message = await message.reply(sending_text)
            messages.append(message)
        except aiogram.exceptions.TelegramBadRequest as exc:
            logger.debug("Could not send response: {!r}. Trying with HTML parse_mode", exc)
            message = await message.reply(sending_text, parse_mode=ParseMode.HTML)
            messages.append(message)
    return messages
