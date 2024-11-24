"""Calling prefixes middleware is defined here"""

import itertools
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Literal

from aiogram import BaseMiddleware
from aiogram.types import Message, ReactionTypeEmoji, TelegramObject
from loguru._logger import Logger


@dataclass
class _Prefix:
    prefix: str
    target: Literal["is_gpt_request", "is_art_request"]


class EmptyMessageError(RuntimeError):
    """Empty message is sent by user, no reaction is needed."""


def _check_generation_commands(message: Message, data: dict[str, Any], prefixes: list[_Prefix]) -> None:
    text = message.text or message.caption or ""

    if text == "":
        data["text"] = ""
        return

    # reply context case
    if (
        message.reply_to_message is not None
        and message.reply_to_message.from_user.id == message.bot.id
        and message.reply_to_message.photo is None
    ):
        data["text"] = text
        data["is_gpt_request"] = True
        return

    # prefix checks
    t_lower = text.lower()
    for p in prefixes:
        if t_lower.startswith(p.prefix):
            data["text"] = text[len(p.prefix) :].strip(", ")
            if data["text"] == "":
                raise EmptyMessageError()
            if p.prefix.startswith("/") and data["text"].startswith("@"):
                if " " not in data["text"]:
                    raise EmptyMessageError()
                data["text"] = data["text"][data["text"].find(" ") + 1 :]
            data[p.target] = True
            return

    # generation by default in direct messages
    if message.chat.type == "private":
        data["text"] = text
        data["is_gpt_request"] = True
        return


class TreatPrefixesMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """Middleware that sets `prefixes` data key with a tuple of given prefixes"""

    def __init__(
        self, gpt_prefixes: Iterable[str], art_prefixes: Iterable[str], should_ignore_func: Callable[[Message], bool]
    ):
        self.prefixes = sorted(
            (
                _Prefix(p.lower(), target)
                for p, target in itertools.chain(
                    zip(gpt_prefixes, itertools.repeat("is_gpt_request")),
                    zip(art_prefixes, itertools.repeat("is_art_request")),
                )
            ),
            key=lambda p: -len(p.prefix),
        )
        self._should_ignore_func = should_ignore_func

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        logger: Logger = data["logger"]
        if isinstance(event, Message):
            if self._should_ignore_func(event):
                logger.info("Skipped")
                return
            try:
                _check_generation_commands(event, data, self.prefixes)
            except EmptyMessageError:
                await event.react([ReactionTypeEmoji(emoji="🤡")])
                return

        return await handler(event, data)
