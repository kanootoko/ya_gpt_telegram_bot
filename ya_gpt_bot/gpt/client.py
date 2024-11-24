"""Abstract GPT client is defined here."""

import abc

from .waiter import AsyncWaiter


class GPTClient(abc.ABC):
    """Abstract GPT client.
    `request` should be called from outside while `_request` is to be implemented.
    """

    def __init__(self, waiter: AsyncWaiter):
        """Initialize with setting waiter."""
        self.waiter = waiter

    @abc.abstractmethod
    async def _request(
        self,
        request_dialog: list[str] | str,
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        **kwargs,
    ) -> str:
        raise NotImplementedError()

    async def request(
        self,
        request_dialog: list[str] | str,
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        **kwargs,
    ) -> str:
        """Perform a request to GPT service getting a result answering the given prompt. If dialog is given,
        it must start and finish with a user message.
        """
        async with self.waiter:
            return await self._request(
                request_dialog, creativity_override, instruction_text_override, timeout_override, **kwargs
            )

    async def close(self) -> None:
        """Free the resources on exit."""


class ArtClient(abc.ABC):
    """Abstract ART client"""

    def __init__(self, waiter: AsyncWaiter):
        """Initialize with setting waiter."""
        self.waiter = waiter

    @abc.abstractmethod
    async def _generate(
        self,
        prompt: str,
        aspect_ratio: float | None = None,
        seed: float | None = None,
        **kwargs,
    ) -> str:
        raise NotImplementedError()

    async def generate(
        self,
        prompt: str,
        aspect_ratio: float | None = None,
        seed: float | None = None,
        **kwargs,
    ) -> bytes:
        """Perform a request to ART service getting a resulting image."""
        async with self.waiter:
            return await self._generate(prompt, aspect_ratio, seed, **kwargs)

    async def close(self) -> None:
        """Free the resources on exit."""
