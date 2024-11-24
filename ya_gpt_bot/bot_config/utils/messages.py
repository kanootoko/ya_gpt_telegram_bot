"""Message helpers are defined here."""

from typing import Callable, Iterable

from aiogram.types import Message


def get_should_ignore_func(prefixes: Iterable[str], postfixes: Iterable[str]) -> Callable[[Message], bool]:
    """Get function to check message prefix/postfix is stated in `prefixes`/`postfixes`."""
    prefixes = tuple(prefixes)
    postfixes = tuple(postfixes)

    def inner(message: Message) -> bool:
        text = message.text or message.caption or ""
        if text.startswith(prefixes) or text.endswith(postfixes):
            return True
        return False

    return inner
