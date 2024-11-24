"""Pydantic models used in text generation requests"""

from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel, Field, model_validator

__all__ = [
    "CompletionOptions",
    "Alternative",
    "TextGenerationRequest",
    "TextGenerationResponse",
]


class ModelUsage(BaseModel):
    """Model usage values on request."""

    inputTextTokens: int
    completionTokens: int
    totalTokens: int


class CompletionOptions(BaseModel):
    """Generation Options values.

    `temperature` is a creativeness setting, 0 is for straightforward answers.
    """

    stream: bool = False
    temperature: float = Field(0.5, ge=0.0, le=1.0)
    maxTokens: int = Field(5000, ge=0.0, le=1.0)


class Message(BaseModel):
    """Single message to pass to YandexGPT completion model"""

    role: Literal["system", "assistant", "user"]
    text: str


class TextGenerationRequest(BaseModel):
    """Request for text generation."""

    modelUri: str
    completionOptions: CompletionOptions
    messages: list[Message] = Field(default_factory=list)

    def add_user_message(self, text: str):
        """Add user message to the request."""
        self.messages: list[Message]
        self.messages.append(Message(role="user", text=text))

    def add_system_message(self, text: str):
        """Add system instruction message to the request."""
        self.messages: list[Message]
        self.messages.append(Message(role="system", text=text))

    def add_assistant_message(self, text: str):
        """Add model reply message to the request."""
        self.messages: list[Message]
        self.messages.append(Message(role="assistant", text=text))


class Alternative(BaseModel):
    """Alternative response for the given prompt."""

    message: Message
    status: str


class TextGenerationResult(BaseModel):
    """Result of text generation method."""

    alternatives: list[Alternative]
    usage: ModelUsage
    modelVersion: str


class TextGenerationError(BaseModel):
    """Result of text generation method."""

    code: int | None = None
    grpc_code: int | None = None
    http_code: int | None = None
    http_status: str | None = None
    message: str
    details: Any


class TextGenerationResponse(BaseModel):
    """Response of text generation method."""

    result: TextGenerationResult | None = None
    error: TextGenerationError | None = None

    @model_validator(mode="before")
    def root_error_message_fix(self: dict[str, Any]) -> None:
        """Fix `{"error": "error message", ...}` structure to `{"error": {"message": "error message"}}`"""
        if "error" in self and isinstance(self["error"], str):
            logger.debug("Fixing error response from YandexGPT: {}", self)
            self["error"] = {
                "message": self.get("message") or self.get("error"),
                "code": self.get("code"),
                "details": self.get("details"),
            }
        return self

    @model_validator(mode="after")
    def non_empty_validator(self) -> None:
        """Check that either `result` or `error` is set."""
        if self.result is None and self.error is None:
            raise ValueError("Error parsing response from TextGeneration method")
        return self
