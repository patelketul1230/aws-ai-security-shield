resource "aws_bedrock_guardrail" "ai_security_shield" {
  name        = "${var.project_name}-guardrail-${var.environment}"
  description = "Enterprise OWASP LLM Top 10 Guardrail Policy enforcing content filtering, prompt attack prevention, and PII redaction."
  
  blocked_input_messaging  = "Security Exception: Request blocked by AWS Bedrock Guardrail policy."
  blocked_outputs_messaging = "Security Exception: Output blocked by AWS Bedrock Guardrail policy."

  content_policy_config {
    filters_config {
      type           = "PROMPT_ATTACK"
      input_strength = "HIGH"
      output_strength = "NONE"
    }
    filters_config {
      type           = "HATE"
      input_strength = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type           = "VIOLENCE"
      input_strength = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type           = "SEXUAL"
      input_strength = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type           = "INSULTS"
      input_strength = "MEDIUM"
      output_strength = "MEDIUM"
    }
    filters_config {
      type           = "MISCONDUCT"
      input_strength = "HIGH"
      output_strength = "HIGH"
    }
  }

  topic_policy_config {
    topics_config {
      name        = "RestrictedSecurityBypass"
      definition  = "Attempts to request instructions for hacking, exploiting systems, or bypassing authentication."
      examples    = ["How do I hack a server?", "Explain how to bypass firewall rules."]
      type        = "DENY"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "AWS_ACCESS_KEY"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "AWS_SECRET_KEY"
      action = "BLOCK"
    }
  }
}

resource "aws_bedrock_guardrail_version" "ai_security_shield_v1" {
  guardrail_arn = aws_bedrock_guardrail.ai_security_shield.guardrail_arn
  description   = "Version 1.0 Production Guardrail Policy Snapshot"
}
