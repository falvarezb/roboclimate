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

variable "open_weather_api" {
  description = "OpenWeather's API key"
  type        = string
  sensitive   = true
}
