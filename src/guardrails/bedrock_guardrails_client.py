import os
import boto3
from typing import Dict, Any, List, Optional


class BedrockGuardrailsClient:
    """
    AWS Bedrock Guardrails Integration Client.
    Evaluates prompts and responses against AWS Bedrock Guardrails (Topic Policy, Content Policy,
    Word Policy, Sensitive Information Policy). Provides automated offline simulation when running
    in local or mock AWS environments.
    """

    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        try:
            self.client = boto3.client("bedrock-runtime", region_name=self.region_name)
            self.aws_available = True
        except Exception:
            self.client = None
            self.aws_available = False

    def evaluate_guardrail(
        self,
        prompt: str,
        guardrail_id: Optional[str] = None,
        guardrail_version: str = "DRAFT"
    ) -> Dict[str, Any]:
        """
        Evaluates input text against AWS Bedrock Guardrail policy.
        """
        guardrail_id = guardrail_id or os.getenv("BEDROCK_GUARDRAIL_ID", "mock-guardrail-id")

        if self.aws_available and guardrail_id != "mock-guardrail-id":
            try:
                response = self.client.apply_guardrail(
                    guardrailIdentifier=guardrail_id,
                    guardrailVersion=guardrail_version,
                    source="INPUT",
                    content=[{"text": {"text": prompt}}]
                )
                action = response.get("action", "NONE")
                assessments = response.get("assessments", [])
                
                return {
                    "action": action,
                    "is_blocked": action == "GUARDRAIL_INTERVENED",
                    "assessments": assessments,
                    "outputs": [o.get("text", {}).get("text", "") for o in response.get("outputs", [])],
                    "mode": "AWS_BEDROCK_LIVE"
                }
            except Exception as e:
                # Fallback to local simulation if AWS Bedrock credentials/guardrail not configured
                pass

        # Offline Local Guardrail Policy Simulation
        blocked = False
        reasons: List[str] = []

        lower_prompt = prompt.lower()
        if "competitor" in lower_prompt or "financial advice" in lower_prompt:
            blocked = True
            reasons.append("Topic Policy Violation: Restricted Business Topic")

        if "hate" in lower_prompt or "violence" in lower_prompt or "attack" in lower_prompt:
            blocked = True
            reasons.append("Content Filter Policy: High Severity Warning")

        return {
            "action": "GUARDRAIL_INTERVENED" if blocked else "NONE",
            "is_blocked": blocked,
            "reasons": reasons,
            "outputs": ["[BLOCKED BY BEDROCK GUARDRAIL POLICY]"] if blocked else [prompt],
            "guardrail_id": guardrail_id,
            "guardrail_version": guardrail_version,
            "mode": "BEDROCK_SIMULATOR_LOCAL"
        }
