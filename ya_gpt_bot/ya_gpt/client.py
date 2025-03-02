"""YandexGPT client is defined here."""

import asyncio
import base64
import json
import time
import traceback

import aiohttp
import pydantic
from loguru import logger as global_logger
from loguru._logger import Logger

from ya_gpt_bot.gpt.client import ArtClient, GPTClient
from ya_gpt_bot.gpt.waiter import AsyncWaiter
from ya_gpt_bot.ya_gpt import exceptions as ya_exc
from ya_gpt_bot.ya_gpt.models.art_generation import ArtGenerationRequest

from .auth_service import AuthService
from .models.common import AsyncGenerationOperationResponse
from .models.text_generation import (
    CompletionOptions,
    TextGenerationError,
    TextGenerationRequest,
    TextGenerationResponse,
    TextGenerationResult,
)
from .waiter import AsyncWaiterDummy

CENSORED_RESULTS = {
    "В интернете есть много сайтов с информацией на эту тему. [Посмотрите, что нашлось в поиске](https://ya.ru)",
}


class DummyGPTClient(GPTClient):
    """
    Dummy impl for local tests
    """

    def __init__(self, waiter: AsyncWaiterDummy, *args, **kwargs):  # pylint: disable=unused-argument
        super().__init__(waiter)

    async def _request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        request_dialog: list[str] | str,
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        logger: Logger = global_logger,  # pylint: disable=unused-argument
        **kwargs,
    ) -> str:
        return "Dummy response"


class YaGPTClient(GPTClient):
    """Yandex GPT sync client with async methods.
    Fetches response within the same session as request is sent.

    Docs: https://yandex.cloud/ru/docs/foundation-models/text-generation/api-ref/TextGeneration/completion
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        folder_id: str,
        auth_service: AuthService,
        waiter: AsyncWaiter,
        host: str = "https://llm.api.cloud.yandex.net",
        model: str = "yandexgpt-lite/latest",
        creativity: float = 0.5,
        instruction_text: str = "",
    ):
        super().__init__(waiter)
        self.host = host.rstrip("/")
        self.session = aiohttp.ClientSession(self.host)
        self.folder_id = folder_id
        self.auth_service = auth_service
        self.model = model
        self.creativity = creativity
        self.instruction_text = instruction_text

    async def close(self) -> None:
        """Close session."""
        await self.session.close()

    async def request_raw(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        request_dialog: list[str],
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        logger: Logger = global_logger,
    ) -> TextGenerationResult | TextGenerationError:
        """Perform a text request to YandexGPT TextGeneration method."""
        response_http_status = 0
        timeout_override = timeout_override or 60
        try:
            request = TextGenerationRequest(
                modelUri=f"gpt://{self.folder_id}/{self.model}",
                completionOptions=CompletionOptions(temperature=creativity_override or self.creativity),
            )
            if instruction_text_override or self.instruction_text:
                request.add_system_message(instruction_text_override or self.instruction_text)
            for i, message in enumerate(request_dialog):
                if i % 2 == 0:
                    request.add_user_message(message)
                else:
                    request.add_assistant_message(message)
            async with self.session.post(
                "/foundationModels/v1/completion",
                headers={
                    "Authorization": f"Bearer {self.auth_service.get_iam()}",
                    "x-folder-id": self.folder_id,
                    "Content-Type": "application/json",
                },
                data=json.dumps(request.model_dump(), ensure_ascii=True),
                timeout=timeout_override,
            ) as response_raw:
                response_text = await response_raw.text()
                logger.trace("YaGPT raw response: {}", response_text)
                response_http_status = response_raw.status
            try:
                response = TextGenerationResponse.model_validate_json(response_text)
            except pydantic.ValidationError as exc:
                logger.debug("Response validation error ({}). Raw response: `{}`", exc, response_text.strip())
                raise
            if response.result.alternatives[0].message.text in CENSORED_RESULTS:
                raise ya_exc.GPTInvalidPrompt()
            if response_http_status != 200:
                if not (response.error.http_code or response.error.code or response.error.grpc_code):
                    response.error.http_code = response_http_status
                return response.error
            return response.result
        except ya_exc.YaGPTError:
            raise
        except Exception as exc:
            logger.error("Could not execute YandexGPT text generation request: {!r}", exc)
            logger.debug("Traceback: {}", traceback.format_exc())
            raise ya_exc.TextGenerationError(response_http_status, str(exc)) from exc

    async def _request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        request_dialog: list[str] | str,
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        logger: Logger = global_logger,
        **kwargs,
    ) -> str:
        if isinstance(request_dialog, str):
            request_dialog = [request_dialog]
        response = await self.request_raw(
            request_dialog, creativity_override, instruction_text_override, timeout_override, logger=logger
        )
        if isinstance(response, TextGenerationError):
            raise ya_exc.TextGenerationError(
                response.http_code or response.code or response.grpc_code, response.message
            )
        return response.alternatives[0].message.text


class AsyncYaGPTClient(GPTClient):
    """Yandex GPT async client with async methods.
    Firstly fetches the request id from generation request and then polls the result.

    Docs: https://yandex.cloud/ru/docs/foundation-models/text-generation/api-ref/TextGenerationAsync/completion

    This is an experimental version as async requests are incredibly slower comparing to sync ones.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        folder_id: str,
        auth_service: AuthService,
        waiter: AsyncWaiter,
        model: str = "yandexgpt-lite/latest",
        host: str = "https://llm.api.cloud.yandex.net",
        creativity: float = 0.5,
        instruction_text: str = "",
    ):
        super().__init__(waiter)
        self.host = host.rstrip("/")
        self.session = aiohttp.ClientSession(self.host)
        self.folder_id = folder_id
        self.auth_service = auth_service
        self.model = model
        self.creativity = creativity
        self.instruction_text = instruction_text

    async def close(self) -> None:
        """Close session."""
        await self.session.close()

    async def request_raw(  # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
        self,
        request_dialog: list[str],
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        logger: Logger = global_logger,
    ) -> TextGenerationResult | TextGenerationError:
        """Perform a text request to YandexGPT TextGeneration method."""
        response_http_status = 0
        timeout_override = timeout_override or 60
        try:
            request = TextGenerationRequest(
                modelUri=f"gpt://{self.folder_id}/{self.model}",
                completionOptions=CompletionOptions(temperature=creativity_override or self.creativity),
            )
            if instruction_text_override or self.instruction_text:
                request.add_system_message(instruction_text_override or self.instruction_text)
            for i, message in enumerate(request_dialog):
                if i % 2 == 0:
                    request.add_user_message(message)
                else:
                    request.add_assistant_message(message)
            async with self.session.post(
                "/foundationModels/v1/completionAsync",
                headers={
                    "Authorization": f"Bearer {self.auth_service.get_iam()}",
                    "x-folder-id": self.folder_id,
                    "Content-Type": "application/json",
                },
                data=json.dumps(request.model_dump(), ensure_ascii=True),
                timeout=timeout_override,
            ) as response_raw:
                response_text = await response_raw.text()
                response_http_status = response_raw.status

            try:
                response = AsyncGenerationOperationResponse.model_validate_json(response_text)
            except pydantic.ValidationError as exc:
                logger.debug("Response validation error ({}). Raw response: `{}`", exc, response_text.strip())
                raise
            if response_http_status != 200:
                raise ya_exc.TextGenerationError(response_http_status, response_text)

            logger.info("Polling response for operation_id={}", response.id)

            polling_start = time.time()
            while time.time() - polling_start < timeout_override:
                async with self.session.get(
                    f"/operations/{response.id}", headers={"Authorization": f"Bearer {self.auth_service.get_iam()}"}
                ) as response_raw:
                    response_text = await response_raw.text()
                    response_http_status = response_raw.status

                if response_http_status != 200:
                    raise ya_exc.TextGenerationError(response_http_status, response_text)

                try:
                    response = AsyncGenerationOperationResponse.model_validate_json(response_text)
                except pydantic.ValidationError as exc:
                    logger.debug("Response validation error ({}). Raw response: `{}`", exc, response_text.strip())
                    raise
                if not response.done:
                    await asyncio.sleep(min(timeout_override / 10, 10))
                    continue

                generation_result = TextGenerationResult.model_validate(response.response)
                return generation_result
            raise ya_exc.GenerationTimeoutError()
        except ya_exc.YaGPTError:
            raise
        except Exception as exc:
            logger.error("Could not execute YandexGPT text generation request: {!r}", exc)
            logger.debug("Traceback: {}", traceback.format_exc())
            raise ya_exc.TextGenerationError(response_http_status, str(exc)) from exc

    async def _request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        request_dialog: list[str] | str,
        creativity_override: float | None = None,
        instruction_text_override: str | None = None,
        timeout_override: int | None = None,
        logger: Logger = global_logger,
        **_kwargs,
    ) -> str:
        if isinstance(request_dialog, str):
            request_dialog = [request_dialog]
        response = await self.request_raw(
            request_dialog, creativity_override, instruction_text_override, timeout_override, logger=logger
        )
        if isinstance(response, TextGenerationError):
            raise ya_exc.TextGenerationError(
                response.http_code or response.code or response.grpc_code, response.message
            )
        return response.alternatives[0].message.text


class YaArtClient(ArtClient):
    """YandexART client
    Fetches request id from generation reuqsts and polls it

    Docs: https://yandex.cloud/ru/docs/foundation-models/image-generation/api-ref/ImageGenerationAsync/generate"""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        folder_id: str,
        auth_service: AuthService,
        waiter: AsyncWaiter,
        model: str,
        host: str = "https://llm.api.cloud.yandex.net",
    ):
        """Initialize with setting waiter."""
        super().__init__(waiter)
        self.model = model.strip("/")
        self.folder_id = folder_id.strip("/")
        self.auth_service = auth_service
        self.host = host.rstrip("/")
        self.session = aiohttp.ClientSession(self.host)

    async def _generate(
        self,
        prompt: str,
        aspect_ratio: float | None = None,
        seed: float | None = None,
        logger: Logger = global_logger,
        **kwargs,
    ) -> str:
        if "request_id" in kwargs:
            request_id = kwargs["request_id"]
            logger.debug("Using request_id={} from outside for prompt: {}", request_id, prompt)
        else:
            logger.debug("Requesting image for prompt: {}", prompt)
            request_id = await self.generation_request(prompt, aspect_ratio, seed)
            logger.info("Starting polling for image for request_id={}", request_id)
        img = await self.poll(request_id)
        logger.info("Polling finished for request_id={}", request_id)
        return img

    async def generation_request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        prompt: str,
        aspect_ratio: float | None = None,
        seed: float | None = None,
        timeout: int = 30,
        logger: Logger = global_logger,
    ) -> str:
        """Perform generation request and return request_id for polling."""

        model = f"art://{self.folder_id}/{self.model}"
        request = ArtGenerationRequest.from_single_message(prompt, model, aspect_ratio, seed)
        logger.debug("Requesting art generation with following request: {}", request)
        async with self.session.post(
            "/foundationModels/v1/imageGenerationAsync",
            headers={
                "Authorization": f"Bearer {self.auth_service.get_iam()}",
                "x-folder-id": self.folder_id,
                "Content-Type": "application/json",
            },
            data=json.dumps(request.model_dump(), ensure_ascii=True),
            timeout=timeout,
        ) as response_raw:
            response_text = await response_raw.text()
            response_http_status = response_raw.status

        if response_http_status != 200:
            try:
                response_json = json.loads(response_text)
                if (
                    "error" in response_json
                    and response_json["error"] == "it is not possible to generate an image from this"
                    " request because it may violate the terms of use"
                ):
                    raise ya_exc.ArtInvalidPrompt()
            except ya_exc.ArtInvalidPrompt:
                raise
            except Exception:  # pylint: disable=broad-except
                pass
            raise ya_exc.ArtGenerationError(response_http_status, response_text)

        res = AsyncGenerationOperationResponse.model_validate_json(response_text)

        return res.id

    async def poll(self, request_id: str, timeout: int = 30, logger: Logger = global_logger) -> bytes:
        """Return raw jpeg image data from request after polling.

        If timeout is reached, GenerationTimeoutError is raised.
        """
        polling_start = time.time()
        try:
            while time.time() - polling_start < timeout:
                async with self.session.get(
                    f"/operations/{request_id}", headers={"Authorization": f"Bearer {self.auth_service.get_iam()}"}
                ) as response_raw:
                    response_text = await response_raw.text()
                    response_http_status = response_raw.status

                if response_http_status != 200:
                    raise ya_exc.ArtGenerationError(response_http_status, response_text)

                try:
                    response = AsyncGenerationOperationResponse.model_validate_json(response_text)
                except pydantic.ValidationError as exc:
                    logger.debug("Response validation error ({}). Raw response: `{}`", exc, response_text.strip())
                    raise
                if not response.done:
                    await asyncio.sleep(min(timeout / 10, 10))
                    continue

                image_jpeg = base64.decodebytes(response.response["image"].encode("utf-8"))
                generation_result = image_jpeg
                return generation_result
            raise ya_exc.GenerationTimeoutError()
        except ya_exc.YaGPTError:
            raise
        except Exception as exc:
            logger.error("Could not execute YandexGPT text generation request: {!r}", exc)
            logger.debug("Traceback: {}", traceback.format_exc())
            raise ya_exc.ArtGenerationError(response_http_status, str(exc)) from exc

    async def close(self) -> None:
        """Free the resources on exit."""
