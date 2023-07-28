# Input variable definitions

variable "aws_region" {
  description = "AWS region for all resources."
  type    = string
  default = "eu-west-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket containing the csv files"
  type    = string
  default = "roboclimate-test"
}

variable "lambda_cidr_subnet1" {
  description = "CIDR block for the subnet used to connect the lambda function to the EFS"
  default     = "172.31.48.0/20"  
}

variable "lambda_az1" {
  description = "Avaliability zone for the subnet used to connect the lambda function to the EFS"  
  default = "eu-west-1a"
}

variable "lambda_cidr_subnet2" {
  description = "CIDR block for the subnet used to connect the lambda function to the EFS"
  default     = "172.31.64.0/20"  
}

variable "lambda_az2" {
  description = "Avaliability zone for the subnet used to connect the lambda function to the EFS"  
  default = "eu-west-1b"
}

variable "open_weather_api" {
  description = "OpenWeather's API key"
  type        = string
  sensitive   = true
}
