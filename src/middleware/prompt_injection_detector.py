import re
from typing import Dict, Any, List, Tuple


class PromptInjectionDetector:
    """
    OWASP LLM01: Prompt Injection Defense Engine.
    Detects Direct Prompt Injections, Indirect Injections, System Prompt Overrides,
    and Jailbreak attempts (e.g. DAN, Developer Mode, System Prompt Exfiltration).
    """

    SUSPICIOUS_PATTERNS = [
        # Direct System Prompt Overrides
        (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directions|prompts|rules)", "System Prompt Override Attempt"),
        (r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)", "System Prompt Override Attempt"),
        (r"forget\s+(all\s+)?(previous|prior)\s+instructions", "System Prompt Override Attempt"),
        (r"you\s+are\s+now\s+in\s+(unrestricted|god|jailbreak|developer)\s+mode", "Jailbreak Mode Activation"),
        (r"do\s+anything\s+now\s*\(dan\)", "DAN Jailbreak Attempt"),
        
        # System Prompt & Internal Secret Exfiltration
        (r"(repeat|print|reveal|output|display)\s+.*?(system\s+prompt|initial\s+instructions|developer\s+notes|hidden\s+rules)", "System Prompt Exfiltration"),
        (r"reveal\s+your\s+hidden\s+(instructions|prompt|rules)", "System Prompt Exfiltration"),
        (r"output\s+the\s+exact\s+prompt\s+above", "System Prompt Exfiltration"),

        # Boundary Breaks & Subshell / Delimiter Injections
        (r"</?system>", "System Tag Injection"),
        (r"</?instruction>", "Instruction Tag Injection"),
        (r"\[INST\]", "LLaMA Instruction Tag Injection"),
        (r"```(bash|sh|cmd|powershell)\s*(curl|wget|nc|netcat|bash|rm -rf|eval)", "Malicious Code Injection Payload"),

        # Dangerous Command Execution & Exfiltration Patterns
        (r"system\(['\"].*?['\"]\)|\bexec\(['\"].*?['\"]\)|\beval\(['\"].*?['\"]\)", "Arbitrary Code Execution Pattern"),
        (r"cat\s+/etc/passwd|cat\s+/etc/shadow|curl\s+http://169\.254\.169\.254", "AWS IMDS Metadata / OS Exfiltration"),
    ]

    def __init__(self, risk_threshold: float = 0.5):
        self.risk_threshold = risk_threshold

    def inspect(self, prompt: str) -> Dict[str, Any]:
        """
        Scans an incoming prompt for prompt injection and jailbreak signatures.

        Returns:
            Dict containing is_flagged, risk_score, detected_threats, and sanitized_prompt.
        """
        if not prompt or not isinstance(prompt, str):
            return {
                "is_flagged": False,
                "risk_score": 0.0,
                "detected_threats": [],
                "sanitized_prompt": prompt or ""
            }

        detected_threats: List[Dict[str, str]] = []
        pattern_matches = 0

        for pattern, threat_name in self.SUSPICIOUS_PATTERNS:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                pattern_matches += 1
                detected_threats.append({
                    "threat_type": threat_name,
                    "matched_pattern": pattern,
                    "snippet": match.group(0)
                })

        # Calculate risk score normalized between 0.0 and 1.0
        risk_score = min(1.0, pattern_matches * 0.5)
        is_flagged = risk_score >= self.risk_threshold

        return {
            "is_flagged": is_flagged,
            "risk_score": round(risk_score, 2),
            "detected_threats": detected_threats,
            "threat_count": len(detected_threats),
            "status": "BLOCKED" if is_flagged else "PASSED"
        }
