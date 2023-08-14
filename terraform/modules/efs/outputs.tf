output "efs_mount_target_sg_id" {  
  value       = aws_security_group.efs_mount_target_sg.id
}

output "lambda_subnet1_id" { 
  value       = aws_subnet.lambda_subnet1.id
}

output "lambda_subnet2_id" { 
  value       = aws_subnet.lambda_subnet2.id
}

output "file_system_id" {
  value = aws_efs_file_system.roboclimate.id
}

output "access_point_id" {
    value = aws_efs_access_point.roboclimate.id
}

output "access_point_arn" {
    value = aws_efs_access_point.roboclimate.arn
}