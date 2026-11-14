import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai SDK is not installed.")


class GeminiClientService:
    """
    Centralized client service for Google Gemini API integration.
    Handles client initialization, configuration, error catching, and usage metrics.
    """

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
        self.model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash').strip()
        self._client = None

        if self.is_configured:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self._client = None

    @property
    def is_configured(self) -> bool:
        """Checks if the SDK is installed and an API key is set."""
        return bool(GENAI_AVAILABLE and self.api_key)

    def generate_content(self, contents, system_instruction=None, temperature=0.7, tools=None):
        """
        Sends content to Gemini and returns the textual response and usage stats.
        Returns a dict: {
            'text': str,
            'tokens_used': int,
            'success': bool,
            'error': str or None
        }
        """
        if not self.is_configured or not self._client:
            return {
                'text': None,
                'tokens_used': 0,
                'success': False,
                'error': 'Gemini API key is not configured.'
            }

        try:
            config_kwargs = {
                'temperature': temperature,
            }
            if system_instruction:
                config_kwargs['system_instruction'] = system_instruction
            if tools:
                config_kwargs['tools'] = tools

            config = types.GenerateContentConfig(**config_kwargs)

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            response_text = ""
            if response and hasattr(response, 'text') and response.text:
                response_text = response.text
            elif response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    response_text = "".join(p.text for p in candidate.content.parts if hasattr(p, 'text') and p.text)

            tokens_used = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = getattr(response.usage_metadata, 'total_token_count', 0) or 0

            return {
                'text': response_text,
                'tokens_used': tokens_used,
                'success': True,
                'error': None
            }

        except Exception as e:
            logger.exception(f"Gemini API generation error: {e}")
            return {
                'text': None,
                'tokens_used': 0,
                'success': False,
                'error': str(e)
            }


# Global singleton instance
gemini_client = GeminiClientService()

