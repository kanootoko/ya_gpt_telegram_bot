"""Response utilities are defined here."""

import aiogram
import aiogram.exceptions
from aiogram import html
from aiogram.enums import ParseMode
from aiogram.types import Message
from loguru import logger

TELEGRAM_MAX_MESSAGE_LENGTH = 4000  # 4096, 96 characters reserve for possible HTML tags escaping


def split_to_multiple_messages(text: str) -> list[str]:
    """Split long message to a multiple messages each having maximum length below `TELEGRAM_MAX_MESSAGE_LENGTH`."""
    texts: list[str] = []
    while len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
        split_index = text[:TELEGRAM_MAX_MESSAGE_LENGTH].rfind("\n")
        if split_index == -1:
            split_index = text[:TELEGRAM_MAX_MESSAGE_LENGTH].rfind(" ")
            if split_index == -1:
                split_index = TELEGRAM_MAX_MESSAGE_LENGTH
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
            message = await message.reply(html.quote(sending_text), parse_mode=ParseMode.HTML)
            messages.append(message)
    return messages
