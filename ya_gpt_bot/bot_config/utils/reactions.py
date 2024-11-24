"""Reaction helper-functions are defined here."""

from aiogram.types import MessageReactionUpdated, ReactionTypeEmoji


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
