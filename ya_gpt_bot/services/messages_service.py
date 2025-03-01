"""User service protocol is defined here."""

from abc import abstractmethod
from typing import Protocol

from ya_gpt_bot.db.operations.messages import DialogEntry


class MessagesService(Protocol):
    """Service to get and update messages."""

    @abstractmethod
    async def get_dialog(self, chat_id: int, reply_id: int) -> list[DialogEntry]:
        """Return status of a user given by id, create a new one with status `PENDING` if not found."""
        raise NotImplementedError()

    @abstractmethod
    async def save_message(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        message_id: int,
        reply_id: int | None,
        chat_id: int,
        text: str,
        from_self: bool,
    ) -> None:
        """Save message (from user talking with GPT or model responsing to user)."""
        raise NotImplementedError()
