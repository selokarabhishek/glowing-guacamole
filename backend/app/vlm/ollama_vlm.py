"""Ollama VLM provider implementation."""
import httpx
import ollama
from app.vlm.base import BaseVLM
from app.models.schemas import VLMRequest, VLMResponse


class OllamaVLM(BaseVLM):
    """Ollama VLM provider for local models."""

    def __init__(self, base_url: str, model: str):
        """Initialize Ollama VLM.

        Args:
            base_url: Ollama server base URL
            model: Ollama model to use
        """
        super().__init__(model)
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)

    async def analyze(self, request: VLMRequest) -> VLMResponse:
        """Analyze image with Ollama.

        Args:
            request: VLM request with image and prompt

        Returns:
            VLM response with analysis

        Raises:
            ValueError: If Ollama not available or model not found
        """
        if not self.is_available():
            raise ValueError("Ollama server not available")

        # Check if model is available
        try:
            models = self.client.list()
            available_models = [m['name'] for m in models.get('models', [])]
            if self.model not in available_models:
                raise ValueError(f"Model {self.model} not found in Ollama. Available: {available_models}")
        except Exception as e:
            raise ValueError(f"Failed to check Ollama models: {e}")

        # Prepare image data
        image_data = request.image_base64

        # Remove data URL prefix if present
        if image_data.startswith("data:"):
            image_data = image_data.split(",", 1)[1]

        # Build prompt with system instruction
        full_prompt = request.prompt
        if request.system_prompt:
            full_prompt = f"{request.system_prompt}\n\n{request.prompt}"

        # Call Ollama
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                    "images": [image_data]
                }
            ]
        )

        return VLMResponse(
            content=response['message']['content'],
            provider=self.provider_name,
            model=self.model,
            tokens_used=None  # Ollama doesn't provide token counts in response
        )

    def is_available(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if Ollama server is reachable
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider identifier
        """
        return "ollama"
