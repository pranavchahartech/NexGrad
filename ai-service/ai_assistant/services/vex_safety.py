import re
from students.models import StudentProfile


class VEXSafetyService:
    """
    Guards VEX against prompt injection, unauthorized cross-student data access,
    and credential leaks.
    """

    INJECTION_PATTERNS = [
        r'(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions',
        r'(?i)disregard\s+(all\s+)?(previous|prior)\s+system\s+prompts',
        r'(?i)reveal\s+(your\s+)?system\s+prompt',
        r'(?i)print\s+(your\s+)?system\s+instruction',
        r'(?i)output\s+(your\s+)?initial\s+prompt',
        r'(?i)what\s+is\s+your\s+api\s*key',
        r'(?i)gemini_api_key',
        r'(?i)dump\s+database',
        r'(?i)select\s+\*\s+from\s+',
        r'(?i)drop\s+table',
    ]

    @classmethod
    def check_input_safety(cls, text: str) -> tuple[bool, str]:
        """
        Validates the user prompt against known jailbreak / prompt injection patterns.
        Returns (is_safe, error_message).
        """
        if not text or not text.strip():
            return False, "Message cannot be empty."

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return False, "I cannot process system override or prompt extraction requests. Let's focus on your engineering career, technical skills, or job search!"

        return True, ""

    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """
        Scans generated output to ensure no secrets or sensitive tokens are emitted.
        """
        if not text:
            return ""

        # Mask API keys if somehow generated
        text = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[MASKED_CREDENTIAL]', text)
        return text

