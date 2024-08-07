variable "weather_lambda_arn" {
  description = "arn of the lambda function 'weather'"
  type        = string  
}

variable "forecast_lambda_arn" {
  description = "arn of the lambda function 'forecast'"
  type        = string  
}

variable "uvi_lambda_arn" {
  description = "arn of the lambda function 'uvi'"
  type        = string  
}

variable "backup_lambda_arn" {
  description = "arn of the lambda function 'backup'"
  type        = string  
}