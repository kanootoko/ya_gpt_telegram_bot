# pylint: disable=invalid-name
"""Bot aiogram routers are located here."""

from .handlers.group import chat_messages_router
from .handlers.common import common_messages_router
from .handlers.direct import direct_messages_router
from .handlers.fallback import fallback_router

routers_list = [
    chat_messages_router,
    common_messages_router,
    direct_messages_router,
    fallback_router,
]

__all__ = [
    "routers_list",
]
