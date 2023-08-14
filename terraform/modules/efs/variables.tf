variable "lambda_cidr_subnet1" {
  description = "CIDR block for the subnet used to connect the lambda function to the EFS"
  type        = string
}

variable "lambda_az1" {
  description = "Avaliability zone for the subnet used to connect the lambda function to the EFS"
  type        = string
}

variable "lambda_cidr_subnet2" {
  description = "CIDR block for the subnet used to connect the lambda function to the EFS"
  type        = string
}

variable "lambda_az2" {
  description = "Avaliability zone for the subnet used to connect the lambda function to the EFS"
  type        = string
}

variable "lwf_path" {
  description = "path of lambda function's working folder (lwf) in the EFS filesystem"
  type        = string
  default     = "/roboclimate"
}