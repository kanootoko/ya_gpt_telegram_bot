"""YaGPT exceptions are defined here."""


class YaGPTError(RuntimeError):
    """Generic YaGPT runtime error."""


class GenerationTimeoutError(YaGPTError):
    """Timeout exceeded."""


class TextGenerationError(YaGPTError):
    """Error happened during text generation request."""

    def __init__(self, status: int, message: str | None = None):
        super().__init__()
        self.stasus = status
        self.message = message

    def __str__(self) -> str:
        return f"TextGenerationError(status: {self.stasus}, message: {self.message})"


class GPTInvalidPrompt(YaGPTError):
    """Error happened during text generation request."""

    def __init__(self):
        super().__init__(
            400,
            "it is not possible to generate response from the given request because it may violate the terms of usage",
        )

    def __str__(self) -> str:
        return "GPTInvalidPrompt()"


class ArtGenerationError(YaGPTError):
    """Error happened during art generation request."""

    def __init__(self, status: int, message: str | None = None):
        super().__init__()
        self.stasus = status
        self.message = message

    def __str__(self) -> str:
        return f"ArtGenerationError(status: {self.stasus}, message: {self.message})"


class ArtInvalidPrompt(ArtGenerationError):
    """Error happened during art generation request."""

    def __init__(self):
        super().__init__(
            400, "it is not possible to generate an image from this request because it may violate the terms of usage"
        )

    def __str__(self) -> str:
        return "ArtInvalidPrompt()"
