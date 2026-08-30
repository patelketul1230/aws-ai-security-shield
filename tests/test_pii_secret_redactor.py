import pytest
from src.middleware.pii_secret_redactor import PIISecretRedactor


@pytest.fixture
def redactor():
    return PIISecretRedactor()


def test_no_sensitive_info(redactor):
    text = "Deploying AWS Lambda function with standard settings."
    res = redactor.redact(text)
    assert res["is_redacted"] is False
    assert res["total_redactions"] == 0
    assert res["redacted_text"] == text


def test_aws_access_key_redaction(redactor):
    text = "Use access key AKIAIOSFODNN7EXAMPLE to authenticate with AWS S3."
    res = redactor.redact(text)
    assert res["is_redacted"] is True
    assert "[REDACTED_AWS_ACCESS_KEY_ID]" in res["redacted_text"]
    assert "AKIAIOSFODNN7EXAMPLE" not in res["redacted_text"]


def test_aws_secret_key_redaction(redactor):
    text = "aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"
    res = redactor.redact(text)
    assert res["is_redacted"] is True
    assert "[REDACTED_AWS_SECRET_KEY]" in res["redacted_text"]


def test_pii_ssn_email_redaction(redactor):
    text = "Contact user john@example.com with SSN 123-45-6789."
    res = redactor.redact(text)
    assert res["is_redacted"] is True
    assert "[REDACTED_EMAIL]" in res["redacted_text"]
    assert "[REDACTED_SSN]" in res["redacted_text"]
