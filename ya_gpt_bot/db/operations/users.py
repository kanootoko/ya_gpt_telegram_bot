"""Users common operations are defined here."""
from typing import Callable

from sqlalchemy import exists, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from ya_gpt_bot.db.entities import t_chats, t_users
from ya_gpt_bot.db.entities.enums import ChatStatus, UserStatus

func: Callable


async def ensure_user_exists(conn: AsyncConnection, user_id: int) -> None:
    """Check user for existance, insert one with `pending` status and `direct=False` otherwise."""
    exist = (await conn.execute(select(exists().where(t_users.c.id == user_id)))).scalar_one()
    if exist:
        return
    await conn.execute(insert(t_users).values(id=user_id, status=UserStatus.PENDING, direct=False))
    await conn.commit()


async def get_user_status(conn: AsyncConnection, user_id: int, direct: bool) -> UserStatus:
    """Return status of a user given by id, create a new one with status `PENDING` if not found."""
    status = (await conn.execute(select(t_users.c.status).where(t_users.c.id == user_id))).scalar_one_or_none()
    if status is None:
        status = UserStatus.PENDING
        await conn.execute(insert(t_users).values(id=user_id, status=status, direct=direct))
    return status


async def get_chat_status(conn: AsyncConnection, chat_id: int) -> ChatStatus:
    """Return status of a chat (group/supergroup/etc) given by id, create a new one with status `PENDING`
    if not found.
    """
    status = (await conn.execute(select(t_chats.c.status).where(t_chats.c.id == chat_id))).scalar_one_or_none()
    if status is None:
        status = ChatStatus.PENDING
        await conn.execute(insert(t_chats).values(id=chat_id, status=status))
    return status


async def set_user_status(conn: AsyncConnection, user_id: int, status: UserStatus) -> None:
    """Set status of the given user, create a new one with the given status is not found."""
    is_updated = (
        await conn.execute(update(t_users).values(status=status, updated_at=func.now()).where(t_users.c.id == user_id))
    ).rowcount == 1
    if not is_updated:
        await conn.execute(insert(t_users).values(id=user_id, status=status, direct=False))


async def set_chat_status(conn: AsyncConnection, chat_id: int, status: ChatStatus) -> None:
    """Set status of the given chat, create a new one with the given status is not found."""
    is_updated = (
        await conn.execute(update(t_chats).values(status=status, updated_at=func.now()).where(t_chats.c.id == chat_id))
    ).rowcount == 1
    if not is_updated:
        await conn.execute(insert(t_chats).values(id=chat_id, status=status))


async def set_user_direct(conn: AsyncConnection, user_id: int) -> None:
    """Set `direct=True` for a user with given id, create a new one with status `PENDING` is not found."""
    is_updated = (
        await conn.execute(update(t_users).values(direct=True, updated=func.now()).where(t_users.c.id == user_id))
    ).rowcount == 1
    if not is_updated:
        await conn.execute(insert(t_users).values(id=user_id, status=UserStatus.PENDING, direct=True))
