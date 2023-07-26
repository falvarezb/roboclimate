provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      name = "t_roboclimate"
    }
  }

}

locals {
  weather = {
    pkg_folder = "weather_pkg"
    artifact = "weather_pkg.zip"
    function_name = "t_roboclimate_weather"    
  }
  lambda_iam_role = "t_roboclimate_weather_role"
  lambda_policy = "AWSLambdaExecute"

}

data "archive_file" "weather" {
  type = "zip"
  source_dir  = "${path.module}/${local.weather.pkg_folder}"
  output_path = "${path.module}/${local.weather.artifact}"
}

resource "aws_lambda_function" "weather" {
  function_name = local.weather.function_name
  runtime = "python3.8"
  handler = "weather_spider.weather_handler"
  role = aws_iam_role.lambda_exec.arn
  filename = "${path.module}/${local.weather.artifact}"
  timeout = 10
  source_code_hash = data.archive_file.weather.output_base64sha256
  publish = true

  environment {
    variables = {
      OPEN_WEATHER_API = var.open_weather_api
      S3_BUCKET_NAME = var.bucket_name    
    }
  }
}

resource "aws_cloudwatch_log_group" "weather" {
  name = "/aws/lambda/${aws_lambda_function.weather.function_name}"

  retention_in_days = 30
}

resource "aws_iam_role" "lambda_exec" {
  name = local.lambda_iam_role

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Sid    = ""
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/${local.lambda_policy}"
}

