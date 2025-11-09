"""Reaction helper-functions are defined here."""

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, MessageReactionUpdated, ReactionTypeEmoji
from loguru._logger import Logger


def has_new_reaction(message_reaction: MessageReactionUpdated, reaction: str | ReactionTypeEmoji) -> bool:
    """Check if reaction has appeard for the first time."""

    if isinstance(reaction, ReactionTypeEmoji):
        emoji = reaction.emoji
    else:
        emoji = reaction
    for react in message_reaction.new_reaction:
        if react.emoji == emoji and react not in message_reaction.old_reaction:
            return True
    return False


async def react_or_pass_on_fail(message: Message, emoji: str | None, logger: Logger) -> None:
    """Set/remove reaction emoji to message, write warning log without raising error on failure."""
    target = [ReactionTypeEmoji(emoji=emoji)] if emoji is not None else []
    try:
        await message.react(target)
    except TelegramBadRequest:
        logger.warning("Could not set reaction {} on message id={}", target, message.message_id)
