data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../"
  output_path = "${path.module}/../lambda_function.zip"
  excludes = [
    "terraform",
    "tests",
    ".venv",
    ".git",
    "docs"
  ]
}

resource "aws_lambda_function" "ai_security_shield" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-${var.environment}"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "src.server.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 15
  memory_size      = 256

  environment {
    variables = {
      BEDROCK_GUARDRAIL_ID      = aws_bedrock_guardrail.ai_security_shield.guardrail_id
      BEDROCK_GUARDRAIL_VERSION = aws_bedrock_guardrail_version.ai_security_shield_v1.version
      ENVIRONMENT               = var.environment
    }
  }
}
