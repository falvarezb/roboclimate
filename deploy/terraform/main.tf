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
  lambda_eni_policy = "AWSLambdaVPCAccessExecutionRole"

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
  # Update the Lambda function whenever the deployment package changes
  source_code_hash = data.archive_file.weather.output_base64sha256
  publish = true

  environment {
    variables = {
      OPEN_WEATHER_API = var.open_weather_api
      S3_BUCKET_NAME = var.bucket_name    
    }
  }

  vpc_config {
    # Every subnet should be able to reach an EFS mount target in the same Availability Zone. Cross-AZ mounts are not permitted
    subnet_ids         = [aws_subnet.lambda_subnet1.id, aws_subnet.lambda_subnet2.id]
    security_group_ids = [aws_security_group.efs_mount_target_sg.id]
  }

  # Specify the file system configuration for connecting to EFS
  file_system_config {
    arn             = aws_efs_file_system.roboclimate.arn
    # Local mount path inside the lambda function's execution environment. Must start with '/mnt/'
    local_mount_path = "/mnt/efs" 
  }

  # Explicitly declare dependency on EFS mount target.
  # When creating or updating Lambda functions, mount target must be in 'available' lifecycle state.
  depends_on = [aws_efs_mount_target.roboclimate_efs_mount_target1, aws_efs_mount_target.roboclimate_efs_mount_target2]
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

resource "aws_iam_role_policy_attachment" "lambda_eni_policy" {
  # policy to create and manage ENIs (Elastic Network Interfaces)
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/${local.lambda_eni_policy}"
}


############## Elastic File System ##########################

#This uses the default VPC.  It WILL NOT delete it on destroy.
resource "aws_default_vpc" "default" {
}

# Create access to the EFS through two subnets in two different AZs for redundancy
resource "aws_subnet" "lambda_subnet1" {
  vpc_id            = aws_default_vpc.default.id
  cidr_block        = var.lambda_cidr_subnet1
  availability_zone = var.lambda_az1
}

resource "aws_subnet" "lambda_subnet2" {
  vpc_id            = aws_default_vpc.default.id
  cidr_block        = var.lambda_cidr_subnet2
  availability_zone = var.lambda_az2
}

# Create a security group for the EFS mount target
resource "aws_security_group" "efs_mount_target_sg" {
  name_prefix = "roboclimate_efs_mount_target_sg"

  vpc_id = aws_default_vpc.default.id

  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = [var.lambda_cidr_subnet1, var.lambda_cidr_subnet2]
  }
}

# Create an Elastic File System (EFS)
resource "aws_efs_file_system" "roboclimate" {
  creation_token = "roboclimate"

}


# Create a mount target for each subnet in each AZ
resource "aws_efs_mount_target" "roboclimate_efs_mount_target1" {
  file_system_id = aws_efs_file_system.roboclimate.id
  subnet_id      = aws_subnet.lambda_subnet1.id
  security_groups = [aws_security_group.efs_mount_target_sg.id]
}

resource "aws_efs_mount_target" "roboclimate_efs_mount_target2" {
  file_system_id = aws_efs_file_system.roboclimate.id
  subnet_id      = aws_subnet.lambda_subnet2.id
  security_groups = [aws_security_group.efs_mount_target_sg.id]
}

# EFS access point used by lambda file system
resource "aws_efs_access_point" "roboclimate" {
  file_system_id = aws_efs_file_system.roboclimate.id

  root_directory {
    path = "/roboclimate"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "777"
    }
  }

  posix_user {
    gid = 1000
    uid = 1000
  }
}
