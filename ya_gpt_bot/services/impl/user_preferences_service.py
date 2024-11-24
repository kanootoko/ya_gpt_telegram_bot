"""User preferences service implementation for PostgreSQL is defined here."""
from sqlalchemy.ext.asyncio import AsyncEngine

import ya_gpt_bot.db.operations.users_preferences as db
from ya_gpt_bot.services.dtos import UserPreferences
from ya_gpt_bot.services.user_preferences_service import UserPreferencesService


class UserPreferencesServicePostgres(UserPreferencesService):
    """Service to get and update user preferences for YandexGPT text generation in PostgreSQL database as storage."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_preferences(self, user_id: int) -> UserPreferences:
        async with self.engine.connect() as conn:
            res = await db.get_preferences(conn, user_id)
            await conn.commit()
            return res

    async def reset_preferences(self, user_id: int) -> None:
        async with self.engine.connect() as conn:
            res = await db.delete_preferences(conn, user_id)
            await conn.commit()
            return res

    async def set_temperature(self, user_id: int, temperature: float) -> None:
        async with self.engine.connect() as conn:
            res = await db.set_temperature(conn, user_id, temperature)
            await conn.commit()
            return res

    async def set_instruction_text(self, user_id: int, instruction_text: str) -> None:
        async with self.engine.connect() as conn:
            res = await db.set_instruction_text(conn, user_id, instruction_text)
            await conn.commit()
            return res

    async def set_request_timeout(self, user_id: int, timeout: int) -> None:
        async with self.engine.connect() as conn:
            res = await db.set_request_timeout(conn, user_id, timeout)
            await conn.commit()
            return res

    async def shutdown(self) -> None:
        await self.engine.dispose()
