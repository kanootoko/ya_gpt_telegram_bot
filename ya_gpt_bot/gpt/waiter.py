"""Waiter abstract class is defined here."""
import abc
from types import TracebackType


class AsyncWaiter(abc.ABC):
    """Class that allows to configure waiting periods between requests. Should be used as an async context manager"""

    @abc.abstractmethod
    async def __aenter__(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        raise NotImplementedError()
