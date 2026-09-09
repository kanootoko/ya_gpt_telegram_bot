"""Images API contract tests; no cloud credentials or paid requests required."""
import asyncio
import base64
import json
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest
import pytest_asyncio

from ya_gpt_bot.ya_gpt.client import YaArtClient
from ya_gpt_bot.ya_gpt import exceptions as exc
from ya_gpt_bot.ya_gpt.models.art_generation import ArtGenerationRequest
from ya_gpt_bot.ya_gpt.waiter import AsyncWaiterDummy


@pytest_asyncio.fixture
async def client():
    instance = YaArtClient("folder", Mock(get_iam=Mock(return_value="test-iam")), AsyncWaiterDummy(), "model")
    await instance.session.close()
    instance.session = Mock(close=AsyncMock())
    yield instance
    await instance.close()


def respond(client, body, status=200):
    response = Mock(status=status, text=AsyncMock(return_value=body))
    context = AsyncMock()
    context.__aenter__.return_value = response
    client.session.post.return_value = context


@pytest.mark.asyncio
async def test_generate(client):
    image = b"raw image bytes"
    respond(client, json.dumps({"data": [{"b64_json": base64.b64encode(image).decode()}]}))
    assert await client.generate("a dog:2.5, city background", 16 / 9) == image
    args, kwargs = client.session.post.call_args
    assert client.host == "https://ai.api.cloud.yandex.net"
    assert args == ("/v1/images/generations",)
    assert kwargs["json"] == {"model": "art://folder/model", "prompt": "a dog:2.5, city background", "size": "16x9"}
    assert kwargs["headers"]["Authorization"] == "Bearer test-iam"
    assert "Content-Type" not in kwargs["headers"]
    assert kwargs["timeout"].total == 120
    client.session.get.assert_not_called()


@pytest.mark.parametrize(("ratio", "size"), [(None, "auto"), (1, "1x1"), (1.5, "3x2"), (2 / 3, "2x3")])
def test_ratio(ratio, size):
    assert ArtGenerationRequest.from_single_message("prompt", "model", ratio).size == size


@pytest.mark.parametrize("ratio", [0, -1, float("inf"), float("nan")])
def test_invalid_ratio(ratio):
    with pytest.raises(ValueError):
        ArtGenerationRequest.from_single_message("prompt", "model", ratio)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body", ["not-json", "{}", '{"data": []}', '{"data": [{"b64_json": "!!"}]}', '{"data": [{"b64_json": null}]}']
)
async def test_invalid_response(client, body):
    respond(client, body)
    with pytest.raises(exc.ArtGenerationError):
        await client.generate("prompt")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("body", "error"),
    [
        ('{"error":{"code":"content_policy_violation","message":"blocked"}}', exc.ArtInvalidPrompt),
        ('{"error":"Я не могу сгенерировать это изображение. Давайте попробуем другую тему."}', exc.ArtInvalidPrompt),
        ("unavailable", exc.ArtGenerationError),
    ],
)
async def test_http_error(client, body, error):
    respond(client, body, 400)
    with pytest.raises(error):
        await client.generate("prompt")


@pytest.mark.asyncio
async def test_timeout(client):
    client.session.post.side_effect = asyncio.TimeoutError
    with pytest.raises(exc.GenerationTimeoutError):
        await client.generate("prompt", timeout=5)
    assert client.session.post.call_args.kwargs["timeout"].total == 5


@pytest.mark.asyncio
async def test_transport_failure(client):
    client.session.post.side_effect = aiohttp.ClientConnectionError
    with pytest.raises(exc.ArtGenerationError):
        await client.generate("prompt")


@pytest.mark.asyncio
async def test_close(client):
    await client.close()
    client.session.close.assert_awaited_once()
