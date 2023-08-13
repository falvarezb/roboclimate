variable "function_name" {
  description = "name of the lambda function"
  type        = string  
}

variable "handler_name" {
  description = "name of the lambda function handler"
  type        = string  
}

variable "execution_role" {
  description = "role assumed by the lambda function when executing"
  type        = string  
}

variable "subnet_ids" {
  description = "ids of the private subnets where EFS is to be mounted"
  type        = list(string)  
}

variable "security_group_ids" {
  description = "ids of the security groups to control access to the mounted EFS"
  type        = list(string)  
}

variable "access_point_arn" {
  description = "arn of the access point to the EFS"
  type        = string 
}


variable "artifact_folder" {
  description = "folder containing files to be packaged"
  type        = string  
}

variable "open_weather_api" {
  description = "OpenWeather's API key"
  type        = string
  sensitive   = true
}

