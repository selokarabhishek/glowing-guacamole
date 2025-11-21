"""Base VLM provider abstract class."""
from abc import ABC, abstractmethod
from app.models.schemas import VLMRequest, VLMResponse


class BaseVLM(ABC):
    """Abstract base class for VLM providers."""

    def __init__(self, model: str):
        """Initialize VLM provider.

        Args:
            model: Model identifier to use
        """
        self.model = model

    @abstractmethod
    async def analyze(self, request: VLMRequest) -> VLMResponse:
        """Analyze image with prompt.

        Args:
            request: VLM request with image and prompt

        Returns:
            VLM response with analysis
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if provider can be used
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider identifier
        """
        pass
