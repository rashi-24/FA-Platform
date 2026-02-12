"""
Hugging Face LLM Service
Provides access to Hugging Face Inference API for general financial insights
SECURITY: Only used for non-PII queries
"""

import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """
    Service for interacting with Hugging Face Inference API
    Uses free tier with rate limits
    """

    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.model = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set. LLM features will be disabled.")

    def query(
        self,
        prompt: str,
        context: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Send query to Hugging Face Inference API

        Args:
            prompt: The question or prompt to send to the model
            context: Optional context to include with the prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        if not self.api_key:
            return "LLM service is not configured. Please set HUGGINGFACE_API_KEY."

        # Build full prompt with context
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:" if context else prompt

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            }
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    return result.get('generated_text', '')
                else:
                    return str(result)

            elif response.status_code == 503:
                # Model is loading
                return "The AI model is currently loading. Please try again in a few moments."

            else:
                error_msg = f"HuggingFace API error: {response.status_code}"
                logger.error(f"{error_msg} - {response.text}")
                raise Exception(error_msg)

        except requests.exceptions.Timeout:
            logger.error("HuggingFace API request timed out")
            return "Request timed out. The AI model may be busy. Please try again."

        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            raise

    def is_model_loaded(self) -> bool:
        """
        Check if model is loaded and ready (warm)

        Returns:
            True if model is ready, False otherwise
        """
        if not self.api_key:
            return False

        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    def sanitize_query(self, query: str) -> tuple[bool, str]:
        """
        Check if query contains PII or client-specific information
        SECURITY: Block queries that request client names, phone numbers, emails

        Args:
            query: User query string

        Returns:
            Tuple of (is_safe, sanitized_query or error_message)
        """
        # List of blocked patterns (case-insensitive)
        blocked_keywords = [
            'client name', 'phone number', 'email address', 'address of',
            'show me client', 'list clients', 'client details',
            'personal information', 'contact information'
        ]

        query_lower = query.lower()

        for keyword in blocked_keywords:
            if keyword in query_lower:
                return False, f"For privacy reasons, I cannot provide specific client information. Please ask general financial questions instead."

        return True, query


# Singleton instance
_llm_service = None


def get_llm_service() -> HuggingFaceService:
    """Get singleton instance of HuggingFace service"""
    global _llm_service
    if _llm_service is None:
        _llm_service = HuggingFaceService()
    return _llm_service
