"""Claude VLM provider implementation."""
import base64
from anthropic import Anthropic
from app.vlm.base import BaseVLM
from app.models.schemas import VLMRequest, VLMResponse


class ClaudeVLM(BaseVLM):
    """Claude VLM provider using Anthropic API."""

    def __init__(self, api_key: str, model: str):
        """Initialize Claude VLM.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        super().__init__(model)
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key) if api_key else None

    async def analyze(self, request: VLMRequest) -> VLMResponse:
        """Analyze image with Claude vision.

        Args:
            request: VLM request with image and prompt

        Returns:
            VLM response with analysis

        Raises:
            ValueError: If API key not configured
        """
        if not self.client:
            raise ValueError("Claude API key not configured")

        # Determine media type from base64 data
        image_data = request.image_base64
        media_type = "image/png"

        # Check if it's a data URL and extract the media type
        if image_data.startswith("data:"):
            # Format: data:image/png;base64,xxxxx
            media_part = image_data.split(";")[0].split(":")[1]
            media_type = media_part
            # Extract just the base64 data
            image_data = image_data.split(",", 1)[1]

        # Build message content with image
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data,
                },
            },
            {
                "type": "text",
                "text": request.prompt,
            }
        ]

        # Call Claude API
        max_tokens = request.max_tokens or 4096
        system_prompt = request.system_prompt or ""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )

        # Extract response
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        return VLMResponse(
            content=response_text,
            provider=self.provider_name,
            model=self.model,
            tokens_used=message.usage.input_tokens + message.usage.output_tokens
        )

    def is_available(self) -> bool:
        """Check if Claude is available.

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
        return "claude"
