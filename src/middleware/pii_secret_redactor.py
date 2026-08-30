import re
from typing import Dict, Any, List


class PIISecretRedactor:
    """
    OWASP LLM06: Sensitive Information Disclosure Defense.
    Provides Zero-Trust edge redaction for AWS Access Keys, Secret Keys, JWT Tokens,
    SSNs, Credit Cards, and PII in both LLM prompts and model responses.
    """

    REDACTION_PATTERNS = [
        # AWS Access Key ID
        (r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_AWS_ACCESS_KEY_ID]", "AWS Access Key ID"),
        
        # AWS Secret Access Key (heuristics for 40-char base64 strings attached to aws_secret or secret_key)
        (r"(?i)(aws_secret_access_key|secret_key|aws_secret)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?", 
         r"\1: '[REDACTED_AWS_SECRET_KEY]'", "AWS Secret Access Key"),

        # Generic API Token / Private Key / JWT
        (r"-----BEGIN (?:RSA|EC|DSA|OPENSSH)? PRIVATE KEY-----[\s\S]*?-----END (?:RSA|EC|DSA|OPENSSH)? PRIVATE KEY-----",
         "[REDACTED_PRIVATE_KEY]", "RSA/PEM Private Key"),
        (r"\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b", "[REDACTED_JWT_TOKEN]", "JSON Web Token (JWT)"),

        # PII: Social Security Number (SSN)
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", "Social Security Number"),

        # PII: Credit Card Numbers (13 to 16 digits)
        (r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CREDIT_CARD]", "Credit Card Number"),

        # PII: Email Address
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", "Email Address"),
    ]

    def redact(self, text: str) -> Dict[str, Any]:
        """
        Scans input text and replaces sensitive secrets and PII with redactor masks.

        Returns:
            Dict containing original_text, redacted_text, total_redactions, and list of redacted_types.
        """
        if not text or not isinstance(text, str):
            return {
                "original_text": text or "",
                "redacted_text": text or "",
                "total_redactions": 0,
                "detected_types": []
            }

        redacted_text = text
        detected_types: List[str] = []
        total_redactions = 0

        for pattern, replacement, type_label in self.REDACTION_PATTERNS:
            matches = re.findall(pattern, redacted_text)
            if matches:
                total_redactions += len(matches)
                if type_label not in detected_types:
                    detected_types.append(type_label)
                redacted_text = re.sub(pattern, replacement, redacted_text)

        return {
            "original_text": text,
            "redacted_text": redacted_text,
            "total_redactions": total_redactions,
            "detected_types": detected_types,
            "is_redacted": total_redactions > 0
        }
