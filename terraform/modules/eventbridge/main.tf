############## Eventbridge Scheduler ##########################

locals {
  eventbridge_iam_role = "roboclimate_eventbridge"
  eventbridge_policy   = "roboclimate_eventbridge"
}


resource "aws_iam_role" "eventbridge_exec" {
  name = local.eventbridge_iam_role

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = ["scheduler.amazonaws.com", "events.amazonaws.com"]
        }
      }
    ]
  })
}

resource "aws_iam_policy" "eventbridge" {
  # a more fine-grained policy than just AWSLambdaRole which allows invoking any lambda function

  name        = local.eventbridge_policy
  description = "policy to allow EventBridge to invoke lambda functions"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["lambda:InvokeFunction"],
        Resource = [var.weather_lambda_arn, "${var.weather_lambda_arn}:*", var.forecast_lambda_arn, "${var.forecast_lambda_arn}:*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eventbridge" {  
  role      = aws_iam_role.eventbridge_exec.name
  policy_arn = aws_iam_policy.eventbridge.arn  
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  bus_name = "roboclimate"

  # if true, automatically creates iam role with permission to invoke lambda functions specified as targets
  # though we are gonna do it manually for didactic purposes
  attach_lambda_policy = false
  lambda_target_arns   = [var.weather_lambda_arn, var.forecast_lambda_arn]

  schedules = {
    weather-lambda = {
      name                = "t-weather-lambda"
      schedule_expression = "cron(0 */3 * * ? *)"
      timezone            = "UTC"
      arn                 = var.weather_lambda_arn
      input               = jsonencode({})
      role_arn = aws_iam_role.eventbridge_exec.arn
    }

    forecast-lambda = {      
      name                = "t-forecast-lambda"
      schedule_expression = "cron(0 22 * * ? *)"
      timezone            = "UTC"
      arn                 = var.forecast_lambda_arn
      input               = jsonencode({})
      role_arn = aws_iam_role.eventbridge_exec.arn
    }    
  }
  
}

