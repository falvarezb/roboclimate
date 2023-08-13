# Output value definitions

output "weather_function_info" {
  description = "Name and version of the weather function."
  value       = module.weather_function.function_info
}

output "forecast_function_info" {
  description = "Name and version of the forecast function."
  value       = module.weather_function.function_info
}

output "nat_public_ip" {
  value = aws_instance.nat_instance.public_ip
}

output "efs_instance_private_ip" {
  value = aws_instance.efs_instance.private_ip
}

output "efs_instance_id" {
  value = aws_instance.efs_instance.id
}

output "efs_id" {
  value = module.efs.file_system_id
}

