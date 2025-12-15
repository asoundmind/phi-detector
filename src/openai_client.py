"""
OpenAI API Client for LLM generation.
Provides high-quality responses for deployed applications.
Cost: ~$0.002 per request (very affordable for demos)
"""

import logging
from typing import Optional
import os

try:
    from openai import OpenAI
except ImportError:
    raise ImportError(
        "openai library not installed. "
        "Install with: pip install openai"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Client for OpenAI API.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI client.

        Args:
            model: OpenAI model to use (default: gpt-4o-mini - fast and cheap)
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.model = model

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning(
                "No OpenAI API key found. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter. "
                "Get key from: https://platform.openai.com/api-keys"
            )

        # Initialize client
        self.client = OpenAI(api_key=self.api_key)

        logger.info(f"Initialized OpenAIClient with model: {model}")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Optional[str]:
        """
        Generate text using OpenAI API.

        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            stream: Whether to stream the response (not implemented)

        Returns:
            Generated text response, or None if error occurs
        """
        try:
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty")

            logger.info(f"Generating response for prompt (length: {len(prompt)} chars)")

            # Call OpenAI Chat Completion API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response and response.choices:
                generated_text = response.choices[0].message.content
                logger.info(f"Generated response (length: {len(generated_text)} chars)")
                logger.info(f"Tokens used: {response.usage.total_tokens}")
                return generated_text.strip()
            else:
                logger.error("Empty response from API")
                return None

        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            raise

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            logger.error(
                "Make sure you have a valid OpenAI API key set. "
                "Get one from: https://platform.openai.com/api-keys"
            )
            return None

    def check_health(self) -> bool:
        """
        Check if OpenAI API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            logger.info("Checking OpenAI API health")

            # Try a simple completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )

            if response and response.choices:
                logger.info("OpenAI API is healthy")
                return True
            else:
                logger.warning("OpenAI API returned empty response")
                return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            logger.error(
                "Make sure you have a valid OpenAI API key. "
                "Get one from: https://platform.openai.com/api-keys"
            )
            return False


if __name__ == "__main__":
    # Example usage
    try:
        # Initialize client
        client = OpenAIClient()

        # Check health
        if client.check_health():
            print("OpenAI API is working!")

            # Generate text
            prompt = "What is machine learning in one sentence?"
            response = client.generate(prompt, max_tokens=100)

            if response:
                print(f"\nPrompt: {prompt}")
                print(f"Response: {response}")
            else:
                print("Failed to generate response")
        else:
            print("OpenAI API is not accessible")

    except Exception as e:
        logger.error(f"Error in main: {e}")
