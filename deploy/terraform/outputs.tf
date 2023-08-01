# Output value definitions

output "function_name" {
  description = "Name of the Lambda function."
  value       = aws_lambda_function.weather.function_name
}

output "function_version" {
  description = "Version of the Lambda function."
  value       = aws_lambda_function.weather.version
}

output "nat_public_ip" {
  value = aws_instance.nat_instance.public_ip
}

output "efs_id" {
  value = aws_efs_file_system.roboclimate.id
}

