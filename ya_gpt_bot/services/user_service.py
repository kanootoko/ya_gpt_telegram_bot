"""User service protocol is defined here."""
from abc import abstractmethod
from typing import Protocol

from ya_gpt_bot.services.dtos import ChatStatus, UserStatus


class UserService(Protocol):
    """Service to get and update user information."""

    @abstractmethod
    async def get_user_status(self, user_id: int, direct: bool) -> UserStatus:
        """Return status of a user given by id, create a new one with status `PENDING` if not found."""
        raise NotImplementedError()

    @abstractmethod
    async def get_chat_status(self, chat_id: int) -> ChatStatus:
        """Return status of a chat (group/supergroup/etc) given by id, create a new one with status `PENDING`
        if not found.
        """
        raise NotImplementedError()

    @abstractmethod
    async def set_user_status(self, user_id: int, status: UserStatus) -> None:
        """Set status of the given user, create a new one with the given status is not found."""
        raise NotImplementedError()

    @abstractmethod
    async def set_chat_status(self, chat_id: int, status: ChatStatus) -> None:
        """Set status of the given chat, create a new one with the given status is not found."""
        raise NotImplementedError()

    @abstractmethod
    async def set_user_direct(self, user_id: int) -> None:
        """Set `direct=True` for a user with given id, create a new one with status `PENDING` is not found."""
        raise NotImplementedError()

    async def shutdown(self) -> None:
        """Free the resources on exit."""
