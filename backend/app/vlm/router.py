"""VLM router with factory pattern for provider management."""
from typing import Dict
from app.vlm.base import BaseVLM
from app.vlm.claude_vlm import ClaudeVLM
from app.vlm.openai_vlm import OpenAIVLM
from app.vlm.ollama_vlm import OllamaVLM
from app.models.schemas import VLMRequest, VLMResponse, ProviderInfo
from app.config import Settings


class VLMRouter:
    """Router for managing multiple VLM providers."""

    def __init__(self, settings: Settings):
        """Initialize VLM router.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.providers: Dict[str, BaseVLM] = {}

        # Initialize all providers
        self._init_providers()

    def _init_providers(self):
        """Initialize all VLM provider instances."""
        # Claude
        self.providers["claude"] = ClaudeVLM(
            api_key=self.settings.anthropic_api_key,
            model=self.settings.claude_model
        )

        # OpenAI
        self.providers["openai"] = OpenAIVLM(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_model
        )

        # Ollama
        self.providers["ollama"] = OllamaVLM(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_model
        )

    def get_provider(self, provider_name: str = None) -> BaseVLM:
        """Get VLM provider instance.

        Args:
            provider_name: Provider to use, defaults to configured default

        Returns:
            VLM provider instance

        Raises:
            ValueError: If provider not found or not available
        """
        if provider_name is None:
            provider_name = self.settings.default_vlm_provider

        if provider_name not in self.providers:
            available = list(self.providers.keys())
            raise ValueError(f"Provider '{provider_name}' not found. Available: {available}")

        provider = self.providers[provider_name]

        if not provider.is_available():
            raise ValueError(f"Provider '{provider_name}' is not available. Check configuration.")

        return provider

    async def analyze(self, request: VLMRequest) -> VLMResponse:
        """Route analysis request to appropriate provider.

        Args:
            request: VLM request with optional provider override

        Returns:
            VLM response from provider
        """
        provider = self.get_provider(request.provider)
        return await provider.analyze(request)

    def list_available_providers(self) -> Dict[str, ProviderInfo]:
        """List all providers and their availability.

        Returns:
            Dict mapping provider name to availability info
        """
        result = {}

        for name, provider in self.providers.items():
            # Determine if API key is required and configured
            requires_key = name in ["claude", "openai"]
            api_key_configured = False

            if name == "claude":
                api_key_configured = bool(self.settings.anthropic_api_key)
            elif name == "openai":
                api_key_configured = bool(self.settings.openai_api_key)
            else:  # ollama
                api_key_configured = True  # No key required

            result[name] = ProviderInfo(
                name=name,
                available=provider.is_available(),
                model=provider.model,
                requires_api_key=requires_key,
                api_key_configured=api_key_configured
            )

        return result
