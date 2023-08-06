# Input variable definitions

variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "eu-west-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket containing the csv files"
  type        = string
  default     = "roboclimate-test"
}

variable "lambda_cidr_subnet1" {
  description = "CIDR block for the subnet used to connect the lambda function to the EFS"
  default     = "172.31.48.0/20"
}

variable "lambda_az1" {
  description = "Avaliability zone for the subnet used to connect the lambda function to the EFS"
  default     = "eu-west-1a"
}

variable "lambda_cidr_subnet2" {
  description = "CIDR block for the subnet used to connect the lambda function to the EFS"
  default     = "172.31.64.0/20"
}

variable "lambda_az2" {
  description = "Avaliability zone for the subnet used to connect the lambda function to the EFS"
  default     = "eu-west-1b"
}

variable "nat_cidr_subnet" {
  description = "CIDR block for the subnet containing the NAT instance"
  default     = "172.31.80.0/20"
}

variable "open_weather_api" {
  description = "OpenWeather's API key"
  type        = string
  sensitive   = true
}

variable "my_ip" {
  description = "my computer's IP"
  type        = string
  sensitive   = true
}

variable "ssh_key_name" {
  description = "name of the ssh key to connect to EC2 instances"
  type        = string
  sensitive   = true
}

variable "lambda_mount_path" {
  description = "local path in lambda function to mount lambda function's working folder of the EFS filesystem"
  type        = string
  default     = "/mnt/efs"
}

variable "bastion_mount_path_to_root" {
  description = "local path in bastion host to mount root of the EFS filesystem"
  type        = string
  default     = "/home/ubuntu/efs/root"
}

variable "bastion_mount_path_to_lwf" {
  description = "local path in bastion host to mount lambda function's working folder (lwf) of the EFS filesystem"
  type        = string
  default     = "/home/ubuntu/efs/lwf"
}

variable "lwf_path" {
  description = "path of lambda function's working folder (lwf) in the EFS filesystem"
  type        = string
  default     = "/roboclimate"
}
