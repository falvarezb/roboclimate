output "function_arn" {
  value = aws_lambda_function.roboclimate.arn
}

output "function_info" {
  description = "Name and version of the Lambda function."
  value       = "${aws_lambda_function.roboclimate.function_name}:${aws_lambda_function.roboclimate.version}"
}