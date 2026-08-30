output "api_endpoint" {
  value       = aws_apigatewayv2_api.http_api.api_endpoint
  description = "Public HTTP API Endpoint URL for AWS AI Security Shield"
}

output "lambda_function_arn" {
  value       = aws_lambda_function.ai_security_shield.arn
  description = "ARN of the AI Security Shield AWS Lambda Function"
}

output "bedrock_guardrail_id" {
  value       = aws_bedrock_guardrail.ai_security_shield.guardrail_id
  description = "AWS Bedrock Guardrail Identifier"
}

output "bedrock_guardrail_version" {
  value       = aws_bedrock_guardrail_version.ai_security_shield_v1.version
  description = "AWS Bedrock Guardrail Version"
}

output "cloudwatch_log_group" {
  value       = aws_cloudwatch_log_group.lambda_log_group.name
  description = "CloudWatch Log Group Name"
}
