"""User service implementation for PostgreSQL database is defined here."""
from sqlalchemy.ext.asyncio import AsyncEngine

import ya_gpt_bot.db.operations.users as db
from ya_gpt_bot.services.dtos import ChatStatus, UserStatus
from ya_gpt_bot.services.user_service import UserService


class UserServicePostgres(UserService):
    """Service to get and update user information based on PostgreSQL database storage."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_user_status(self, user_id: int, direct: bool) -> UserStatus:
        async with self.engine.connect() as conn:
            res = await db.get_user_status(conn, user_id, direct)
            await conn.commit()
            return res

    async def get_chat_status(self, chat_id: int) -> ChatStatus:
        async with self.engine.connect() as conn:
            res = await db.get_chat_status(conn, chat_id)
            await conn.commit()
            return res

    async def set_user_status(self, user_id: int, status: UserStatus) -> None:
        async with self.engine.connect() as conn:
            res = await db.set_user_status(conn, user_id, status)
            await conn.commit()
            return res

    async def set_chat_status(self, chat_id: int, status: ChatStatus) -> None:
        async with self.engine.connect() as conn:
            res = await db.set_chat_status(conn, chat_id, status)
            await conn.commit()
            return res

    async def set_user_direct(self, user_id: int) -> None:
        async with self.engine.connect() as conn:
            res = await db.set_user_direct(conn, user_id)
            await conn.commit()
            return res

    async def shutdown(self) -> None:
        await self.engine.dispose()
