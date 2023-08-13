locals {
  lambda_mount_path = "/mnt/efs"
  artifact_folder = "${path.root}/${var.artifact_folder}"
}

data "archive_file" "roboclimate" {
  type        = "zip"
  source_dir  = local.artifact_folder
  output_path = "${local.artifact_folder}.zip"
}



resource "aws_lambda_function" "roboclimate" {
  function_name = var.function_name
  runtime       = "python3.8"
  handler       = var.handler_name
  role          = var.execution_role
  filename      = data.archive_file.roboclimate.output_path
  timeout       = 60
  # Update the Lambda function whenever the deployment package changes
  source_code_hash = data.archive_file.roboclimate.output_base64sha256
  publish          = true

  environment {
    variables = {
      OPEN_WEATHER_API           = var.open_weather_api      
      
      # EFS mount path inside lambda function's execution environment
      # Must start with '/mnt/'
      ROBOCLIMATE_CSV_FILES_PATH = local.lambda_mount_path
    }
  }

  vpc_config {
    # Every subnet should be able to reach an EFS mount target in the same Availability Zone. Cross-AZ mounts are not permitted
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  # Specify the file system configuration for connecting to EFS
  file_system_config {
    arn = var.access_point_arn
    # Local mount path inside the lambda function's execution environment. Must start with '/mnt/'
    local_mount_path = local.lambda_mount_path
  }
}

resource "aws_cloudwatch_log_group" "roboclimate" {
  name = "/aws/lambda/${var.function_name}"

  retention_in_days = 30
}