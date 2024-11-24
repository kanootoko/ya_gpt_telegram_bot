"""Users preferences operations are defined here."""

from typing import Callable

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from ya_gpt_bot.db.entities import t_user_preferences
from ya_gpt_bot.db.operations.users import ensure_user_exists
from ya_gpt_bot.services.dtos import UserPreferences

func: Callable


async def get_preferences(conn: AsyncConnection, user_id: int) -> UserPreferences:
    """Return preferences of the given user. Even if there are no preferences set,
    returns empty UserPreferences object.
    """
    await ensure_user_exists(conn, user_id)
    preferences = (
        (await conn.execute(select(t_user_preferences).where(t_user_preferences.c.user_id == user_id)))
        .mappings()
        .one_or_none()
    )
    if preferences is None:
        return UserPreferences()
    return UserPreferences(preferences["temperature"], preferences["instruction_text"], preferences["timeout"])


async def delete_preferences(conn: AsyncConnection, user_id: int) -> None:
    """Delete preferences of the given user. Do nothing if no preferences exist."""
    await conn.execute(delete(t_user_preferences).where(t_user_preferences.c.user_id == user_id))


async def set_temperature(conn: AsyncConnection, user_id: int, temperature: float) -> None:
    """Set user temperature preference."""
    await ensure_user_exists(conn, user_id)
    res = await conn.execute(
        update(t_user_preferences).values(temperature=temperature).where(t_user_preferences.c.user_id == user_id)
    )
    if res.rowcount == 0:
        await conn.execute(insert(t_user_preferences).values(temperature=temperature, user_id=user_id))


async def set_instruction_text(conn: AsyncConnection, user_id: int, instruction_text: str) -> None:
    """Set user instruction text preference."""
    await ensure_user_exists(conn, user_id)
    if instruction_text == "":
        instruction_text = None
    res = await conn.execute(
        update(t_user_preferences)
        .values(instruction_text=instruction_text)
        .where(t_user_preferences.c.user_id == user_id)
    )
    if res.rowcount == 0:
        await conn.execute(insert(t_user_preferences).values(instruction_text=instruction_text, user_id=user_id))


async def set_request_timeout(conn: AsyncConnection, user_id: int, timeout: int) -> None:
    """Set user timeout preference for YandexGPT request (used for debug purposes mostly)."""
    await ensure_user_exists(conn, user_id)
    res = await conn.execute(
        update(t_user_preferences).values(timeout=timeout).where(t_user_preferences.c.user_id == user_id)
    )
    if res.rowcount == 0:
        await conn.execute(insert(t_user_preferences).values(timeout=timeout, user_id=user_id))
