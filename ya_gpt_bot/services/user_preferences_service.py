"""User preferences service protocol is defined here."""
from abc import abstractmethod
from typing import Protocol

from ya_gpt_bot.services.dtos import UserPreferences


class UserPreferencesService(Protocol):
    """Service to get and update user preferences for YandexGPT text generation."""

    @abstractmethod
    async def get_preferences(self, user_id: int) -> UserPreferences:
        """Return preferences of the given user. Even if there are no preferences set,
        returns empty UserPreferences object.
        """
        raise NotImplementedError()

    @abstractmethod
    async def reset_preferences(self, user_id: int) -> None:
        """Reset preferences to default of the given user. Do nothing if no preferences exist."""
        raise NotImplementedError()

    @abstractmethod
    async def set_temperature(self, user_id: int, temperature: float) -> None:
        """Set user temperature preference."""
        raise NotImplementedError()

    @abstractmethod
    async def set_instruction_text(self, user_id: int, instruction_text: str) -> None:
        """Set user instruction text preference."""
        raise NotImplementedError()

    @abstractmethod
    async def set_request_timeout(self, user_id: int, timeout: int) -> None:
        """Set user timeout preference for YandexGPT request (used for debug purposes mostly)."""
        raise NotImplementedError()

    async def shutdown(self) -> None:
        """Free the resources on exit."""
