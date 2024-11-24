"""Waiter implementations are located here."""
import asyncio
import time
from collections import deque
from types import TracebackType

from ya_gpt_bot.gpt.waiter import AsyncWaiter


class AsyncWaiterDummy(AsyncWaiter):
    """Waiter imitation without real limitations."""

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        pass


class AsyncWaiterLock(AsyncWaiter):
    """Waiter with `asynco.Lock` + `asyncio.sleep` usage."""

    def __init__(self, max_requests_per_second: float, simultanious_requests: int = 1):
        self.simultanious_requests = simultanious_requests
        self.window = 10
        self.rps = int(max_requests_per_second * self.window)
        if self.rps <= 0:
            raise ValueError("Minimal value for `max_requests_per_second argument` is 0.1")
        self.requests: deque[float] = deque()
        """Last requests `time.time`s in a window of `self.window` seconds."""
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(simultanious_requests)

    async def actualize(self) -> None:
        """Remove old requests time from the requests deque."""
        async with self.lock:
            irrelevant_time = time.time() - self.window
            while len(self.requests) > 0 and self.requests[0] < irrelevant_time:
                self.requests.popleft()

    async def __aenter__(self) -> None:
        await self.actualize()
        while (len(self.requests) + 1) / self.window > self.rps:
            cur_time = time.time()
            await asyncio.sleep(max(self.requests[0] - (cur_time - self.window), 0.1))
            await self.actualize()

        async with self.lock:
            await self.semaphore.acquire()
            self.requests.append(time.time())

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        self.semaphore.release()
