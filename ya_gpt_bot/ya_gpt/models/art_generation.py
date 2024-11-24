"""Pydantic models for art generation requests"""

import random
import re

from pydantic import BaseModel, field_validator


class ArtGenerationOptions(BaseModel):
    """Generation options model for art generation request."""

    seed: int

    @field_validator("seed", mode="before")
    @staticmethod
    def fill_seed(seed: int | None) -> int:
        """fill seed with random number if it is not given"""
        if seed is not None:
            return seed
        return random.randint(0, (1 << 63) - 1)


class ArtGenerationRatioOption(BaseModel):  # pylint: disable=too-few-public-methods
    """Aspect ratio setting for art generation."""

    widthRatio: float
    heightRatio: float

    @classmethod
    def from_aspect(cls, aspect: float | None) -> "ArtGenerationRatioOption":
        """Build ratio from aspect"""
        if aspect is None:
            aspect = 1.0
        if aspect >= 1:
            return cls(widthRatio=aspect, heightRatio=1.0)
        return cls(widthRatio=1.0, heightRatio=1 / aspect)


class ArtGenerationMessage(BaseModel):
    """Art generation message model."""

    weight: float
    text: str


weight_re = re.compile(r"^.*:[0-9]{0,1}\.?[0-9]+$")


class ArtGenerationRequest(BaseModel):
    """Request model for art generation."""

    modelUri: str
    generationOptions: ArtGenerationOptions
    messages: list[ArtGenerationMessage]
    aspectRatio: ArtGenerationRatioOption

    @classmethod
    def from_single_message(
        cls, prompt: str, model_uri: str, aspect_ratio: float | None, seed: int | None
    ) -> "ArtGenerationRequest":
        """Split the given prompt message to parts by comma, use semicolon with numbers as weight modifier.

        Example:
        - "a dog:2.5, city background" -> [("a dog", weight: 2.5), ("city background", weight: 1)]"""
        messages: list[ArtGenerationMessage] = []
        for message in map(str.strip, prompt.split(",")):
            weight = 1
            if weight_re.match(message) is not None:
                weight = float(message[message.rfind(":") + 1 :])
                message = message[: message.rfind(":")]
            messages.append(ArtGenerationMessage(weight=weight, text=message))

        return cls(
            modelUri=model_uri,
            generationOptions=ArtGenerationOptions(seed=seed),
            messages=messages,
            aspectRatio=ArtGenerationRatioOption.from_aspect(aspect_ratio),
        )
