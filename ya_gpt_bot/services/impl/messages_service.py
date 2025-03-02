"""User service protocol is defined here."""

from sqlalchemy.ext.asyncio import AsyncEngine

import ya_gpt_bot.db.operations.messages as db
from ya_gpt_bot.db.operations.messages import DialogEntry
from ya_gpt_bot.services.messages_service import MessagesService


class MessagesServicePostgres(MessagesService):
    """Service to get and update messages."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_dialog(self, chat_id: int, reply_id: int) -> list[DialogEntry]:
        """Return status of a user given by id, create a new one with status `PENDING` if not found."""
        async with self.engine.connect() as conn:
            return await db.get_dialog(conn, chat_id, reply_id)

    async def save_message(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        message_id: int,
        reply_id: int | None,
        chat_id: int,
        text: str,
        from_self: bool,
    ) -> None:
        """Save message (from user talking with GPT or model responsing to user)."""
        async with self.engine.connect() as conn:
            await db.save_message(conn, message_id, reply_id, chat_id, text, from_self)
