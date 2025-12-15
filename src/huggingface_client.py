"""
Hugging Face Inference API Client for LLM generation.
Free tier: 1000 requests/hour - perfect for demos!
"""

import logging
from typing import Optional
import os

try:
    from huggingface_hub import InferenceClient
except ImportError:
    raise ImportError(
        "huggingface_hub library not installed. "
        "Install with: pip install huggingface_hub"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HuggingFaceClient:
    """
    Client for Hugging Face Inference API (free tier).
    """

    def __init__(
        self,
        model: str = "meta-llama/Llama-3.2-3B-Instruct",
        api_key: Optional[str] = None
    ):
        """
        Initialize Hugging Face client.

        Args:
            model: Model to use (default: Mistral-7B-Instruct)
            api_key: HuggingFace API token (or set HF_TOKEN env var)
        """
        self.model = model

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("HF_TOKEN")

        if not self.api_key:
            logger.warning(
                "No HuggingFace API token found. "
                "Set HF_TOKEN environment variable or pass api_key parameter. "
                "Get token from: https://huggingface.co/settings/tokens"
            )

        # Initialize client
        self.client = InferenceClient(token=self.api_key)

        logger.info(f"Initialized HuggingFaceClient with model: {model}")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Optional[str]:
        """
        Generate text using Hugging Face Inference API.

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

            # Call Hugging Face Chat Completion API (for conversational models)
            messages = [
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response and response.choices:
                generated_text = response.choices[0].message.content
                logger.info(f"Generated response (length: {len(generated_text)} chars)")
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
                "Make sure you have a valid HuggingFace token set. "
                "Get one from: https://huggingface.co/settings/tokens"
            )
            return None

    def check_health(self) -> bool:
        """
        Check if Hugging Face API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            logger.info("Checking Hugging Face API health")

            # Try a simple chat completion
            messages = [{"role": "user", "content": "Hello"}]
            test_response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=5
            )

            if test_response and test_response.choices:
                logger.info("Hugging Face API is healthy")
                return True
            else:
                logger.warning("Hugging Face API returned empty response")
                return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            logger.error(
                "Make sure you have a valid HuggingFace token. "
                "Get one from: https://huggingface.co/settings/tokens"
            )
            return False


if __name__ == "__main__":
    # Example usage
    try:
        # Initialize client
        client = HuggingFaceClient()

        # Check health
        if client.check_health():
            print("Hugging Face API is working!")

            # Generate text
            prompt = "What is machine learning in one sentence?"
            response = client.generate(prompt, max_tokens=100)

            if response:
                print(f"\nPrompt: {prompt}")
                print(f"Response: {response}")
            else:
                print("Failed to generate response")
        else:
            print("Hugging Face API is not accessible")

    except Exception as e:
        logger.error(f"Error in main: {e}")
