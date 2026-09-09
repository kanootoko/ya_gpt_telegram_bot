"""Image editing routing, source selection and ART authorization."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Message

from ya_gpt_bot.bot_config.handlers.common import art_generation_request, responses
from ya_gpt_bot.bot_config.middlewares.generation_request import TreatPrefixesMiddleware, _check_generation_commands
from ya_gpt_bot.config.app_config import TgBotConfig
from ya_gpt_bot.db.entities.enums import UserStatus, ChatStatus


def message(photo=None, document=None, reply=None, chat_type="private"):
    return SimpleNamespace(
        photo=photo,
        document=document,
        reply_to_message=reply,
        from_user=SimpleNamespace(id=1),
        chat=SimpleNamespace(id=2, type=chat_type),
        text="/img2img make blue",
        bot=SimpleNamespace(download=AsyncMock()),
        reply=AsyncMock(),
        react=AsyncMock(),
        reply_photo=AsyncMock(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["photo", "document", "reply_photo", "reply_document", "both"])
async def test_edit_source(kind):
    photo = SimpleNamespace(file_id="photo")
    document = SimpleNamespace(file_id="doc", file_name="original.png", mime_type="image/png")
    msg = message()
    if kind in ("photo", "both"):
        msg.photo = [SimpleNamespace(file_id="small"), photo]
    if kind == "document":
        msg.document = document
    if kind in ("reply_photo", "both"):
        msg.reply_to_message = message(photo=[photo])
    if kind == "reply_document":
        msg.reply_to_message = message(document=document)

    async def download(attachment, destination):
        assert attachment is (document if "document" in kind else photo)
        destination.write(b"original")

    msg.bot.download.side_effect = download
    service = SimpleNamespace(get_user_status=AsyncMock(return_value=UserStatus.AUTHORIZED))
    client = SimpleNamespace(edit=AsyncMock(return_value=b"result"), generate=AsyncMock())
    await art_generation_request(msg, service, client, "make blue", is_edit_request=True)
    assert client.edit.await_args.args == ("make blue", b"original")
    client.generate.assert_not_called()
    msg.reply_photo.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("document", [None, SimpleNamespace(mime_type="application/pdf")])
async def test_missing_image(document):
    msg = message(document=document)
    service = SimpleNamespace(get_user_status=AsyncMock(return_value=UserStatus.AUTHORIZED))
    client = Mock(edit=AsyncMock())
    await art_generation_request(msg, service, client, "edit", is_edit_request=True)
    msg.reply.assert_awaited_once_with(responses.missing_original_image)
    msg.bot.download.assert_not_called()
    client.edit.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "chat", "allowed"),
    [
        (UserStatus.BLOCKED, "private", False),
        (UserStatus.UNAUTHORIZED, "private", False),
        (UserStatus.UNAUTHORIZED, "group", True),
        (UserStatus.BLOCKED, "group", False),
    ],
)
async def test_art_permissions(status, chat, allowed):
    msg = message(photo=[Mock()], chat_type=chat)
    msg.bot.download.side_effect = lambda attachment, destination: destination.write(b"source")
    service = SimpleNamespace(
        get_user_status=AsyncMock(return_value=status), get_chat_status=AsyncMock(return_value=ChatStatus.AUTHORIZED)
    )
    client = Mock(edit=AsyncMock(return_value=b"result"))
    await art_generation_request(msg, service, client, "edit", is_edit_request=True)
    assert client.edit.await_count == int(allowed)
    assert msg.bot.download.await_count == int(allowed)


@pytest.mark.parametrize("caption", [False, True])
@pytest.mark.parametrize("chat", ["private", "group"])
def test_explicit_edit_overrides_bot_reply(caption, chat):
    raw = dict(
        message_id=1,
        date=0,
        chat={"id": 2, "type": chat},
        reply_to_message={
            "message_id": 2,
            "date": 0,
            "chat": {"id": 2, "type": chat},
            "from": {"id": 99, "is_bot": True, "first_name": "bot"},
        },
    )
    raw["caption" if caption else "text"] = "/img2img@bot make blue"
    msg = Message.model_validate(raw).as_(SimpleNamespace(id=99))
    middleware = TreatPrefixesMiddleware(["/img"], [], lambda _: False, ["/img2img"])
    data = {}
    _check_generation_commands(msg, data, middleware.prefixes)
    assert data == {"text": "make blue", "is_gpt_request": False, "is_art_request": True, "is_edit_request": True}


def test_default_edit_prefix():
    assert TgBotConfig("token").edit_trigger_prefixes == ["/img2img"]
