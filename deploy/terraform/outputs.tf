# Output value definitions

output "function_name" {
  description = "Name of the Lambda function."
  value = aws_lambda_function.weather.function_name
}

output "function_version" {
  description = "Version of the Lambda function."
  value = aws_lambda_function.weather.version
}

