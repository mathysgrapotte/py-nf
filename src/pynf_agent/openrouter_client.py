"""
OpenRouter client for LLM interactions.

Provides a wrapper around the OpenAI client configured to use OpenRouter's API.
"""

import os
from typing import Optional
from openai import OpenAI


class OpenRouterClient:
    """Client for interacting with LLMs via OpenRouter API."""

    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model identifier (defaults to claude-3.5-sonnet)
            base_url: API base URL (defaults to OpenRouter endpoint)
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.model = model or os.environ.get("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or self.OPENROUTER_BASE_URL

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def create_completion(self, messages: list, **kwargs) -> dict:
        """
        Create a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call

        Returns:
            API response dict
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            raise RuntimeError(f"OpenRouter API error: {e}") from e

    def get_model_info(self) -> dict:
        """Get information about the configured model."""
        return {
            "model": self.model,
            "base_url": self.base_url
        }
