"""OpenAI VLM provider implementation."""
from openai import OpenAI
from app.vlm.base import BaseVLM
from app.models.schemas import VLMRequest, VLMResponse


class OpenAIVLM(BaseVLM):
    """OpenAI VLM provider using GPT-4 Vision."""

    def __init__(self, api_key: str, model: str):
        """Initialize OpenAI VLM.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        super().__init__(model)
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key else None

    async def analyze(self, request: VLMRequest) -> VLMResponse:
        """Analyze image with OpenAI vision.

        Args:
            request: VLM request with image and prompt

        Returns:
            VLM response with analysis

        Raises:
            ValueError: If API key not configured
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")

        # Prepare image data
        image_data = request.image_base64

        # Ensure it's in data URL format
        if not image_data.startswith("data:"):
            # Assume PNG if no format specified
            image_data = f"data:image/png;base64,{image_data}"

        # Build messages with image
        messages = []

        # Add system message if provided
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })

        # Add user message with image
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data
                    }
                },
                {
                    "type": "text",
                    "text": request.prompt
                }
            ]
        })

        # Call OpenAI API
        max_tokens = request.max_tokens or 4096

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
        )

        # Extract response
        response_text = response.choices[0].message.content

        return VLMResponse(
            content=response_text,
            provider=self.provider_name,
            model=self.model,
            tokens_used=response.usage.total_tokens
        )

    def is_available(self) -> bool:
        """Check if OpenAI is available.

        Returns:
            True if API key is configured
        """
        return bool(self.api_key and self.client)

    @property
    def provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider identifier
        """
        return "openai"
