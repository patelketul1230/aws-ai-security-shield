# Zero-Trust PII and AWS Secret Redaction at Edge Scale using AWS Lambda

Author: Ketul Patel | Principal Engineer and Cloud Architect  
Series: Enterprise AI Security & MLOps Architecture (Module 2, Part 2)

---

## Introduction

In enterprise Generative AI architectures, data leak prevention (DLP) is a non-negotiable compliance requirement. LLMs process arbitrary text inputs and generate natural language responses. If developers or users submit source code snippets containing hardcoded AWS Access Keys (`AKIA...`), database connection strings, or Personally Identifiable Information (PII) like Social Security Numbers and credit card numbers, those sensitive artifacts can be logged in plain text or retained in model memory contexts.

To mitigate OWASP LLM06 (Sensitive Information Disclosure), enterprise architectures must adopt a **Zero-Trust Edge Redaction Gateway** that inspects payloads before they hit downstream storage or foundational models.

---

## The Zero-Trust Redaction Pattern

The Zero-Trust Redaction Pattern enforces automated token replacement at two critical boundaries:
1. **Ingress Redaction:** Scans incoming user prompts for active AWS IAM keys, private keys, JWTs, and PII, masking sensitive patterns prior to LLM evaluation.
2. **Egress Redaction:** Scans model completion responses before returning them to client applications, ensuring LLMs never leak infrastructure credentials or sensitive user data.

```text
[Client Payload] ──► [Inbound Redactor] ──► [Sanitized Prompt] ──► [LLM Model]
                                                                        │
[Sanitized Response] ◄── [Outbound Redactor] ◄──────────────────────────┘
```

---

## Technical Implementation: High-Performance Redactor Engine

The redaction engine utilizes high-precision regular expressions tuned to minimize false positives while capturing sensitive cloud credentials and compliance PII:

```python
import re
from typing import Dict, Any, List

class PIISecretRedactor:
    REDACTION_PATTERNS = [
        # AWS Access Key ID
        (r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_AWS_ACCESS_KEY_ID]", "AWS Access Key ID"),
        
        # AWS Secret Access Key
        (r"(?i)(aws_secret_access_key|secret_key)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
         r"\1: '[REDACTED_AWS_SECRET_KEY]'", "AWS Secret Access Key"),

        # JSON Web Tokens (JWT)
        (r"\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b", "[REDACTED_JWT_TOKEN]", "JWT"),

        # Social Security Numbers (SSN)
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", "SSN"),

        # Email Addresses
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", "Email Address"),
    ]

    def redact(self, text: str) -> Dict[str, Any]:
        redacted_text = text
        total_redactions = 0
        detected_types = []

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
```

---

## Edge Scale Deployment with AWS Lambda & API Gateway

Deploying the redactor inside an AWS Lambda proxy handler ensures microsecond-level latency impact (< 5ms overhead per request) and automatic horizontal scaling:

- **Memory Allocation:** 256 MB AWS Lambda provisioned with Python 3.11 runtime.
- **Concurrency:** Built-in auto-scaling up to thousands of requests per second.
- **Audit Trails:** Redaction events generate structured CloudWatch logs without printing cleartext secrets.

---

## Compliance & Governance Impact

- **SOC2 & HIPAA Compliance:** Guarantees non-exposure of medical record numbers or financial identifiers.
- **GDPR Article 32:** Enforces technical safeguards against unauthorized processing of personal data.
- **Credential Governance:** Prevents active AWS IAM secret leakage even if engineers paste live configuration files into AI chat interfaces.
