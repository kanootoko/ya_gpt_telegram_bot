"""Request model for the OpenAI-compatible Images API."""

import math
from fractions import Fraction

from pydantic import BaseModel


class ArtGenerationRequest(BaseModel):
    """Only supported Images generation parameters."""

    model: str
    prompt: str
    size: str = "auto"

    @classmethod
    def from_single_message(
        cls, prompt: str, model_uri: str, aspect_ratio: float | None = None
    ) -> "ArtGenerationRequest":
        """Preserve the prompt verbatim and encode the ratio as positive integers."""
        size = "auto"
        if aspect_ratio is not None:
            if not math.isfinite(aspect_ratio) or aspect_ratio <= 0:
                raise ValueError("aspect_ratio must be finite and positive")
            ratio = Fraction(aspect_ratio).limit_denominator(10000)
            if ratio.numerator == 0:
                raise ValueError("aspect_ratio is too small")
            size = f"{ratio.numerator}x{ratio.denominator}"
        return cls(model=model_uri, prompt=prompt, size=size)
