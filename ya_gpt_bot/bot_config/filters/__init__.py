"""aiogram message filters are defined here."""

from aiogram.filters import BaseFilter
from aiogram.types import Message


class DirectMessage(BaseFilter):
    """Filters messages directly from users."""

    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"


class GPTGenerationRequest(BaseFilter):
    """Filters messages which contain text generation request."""

    async def __call__(self, _: Message, is_gpt_request: bool = False) -> bool:
        return is_gpt_request


class ArtGenerationRequest(BaseFilter):
    """Filters messages which contain art generation request."""

    async def __call__(self, _: Message, is_art_request: bool = False) -> bool:
        return is_art_request
