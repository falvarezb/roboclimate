# https://docs.aws.amazon.com/lambda/latest/dg/welcome.html

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
      ROBOCLIMATE_CSV_FILES_PATH = var.lambda_mount_path
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
    local_mount_path = var.lambda_mount_path
  }

  # Explicitly declare dependency on EFS mount target.
  # When creating or updating Lambda functions, mount target must be in 'available' lifecycle state.
  depends_on = [aws_efs_mount_target.roboclimate_efs_mount_target1, aws_efs_mount_target.roboclimate_efs_mount_target2]
}

resource "aws_cloudwatch_log_group" "weather" {
  name = "/aws/lambda/${aws_lambda_function.weather.function_name}"

  retention_in_days = 30
}

# Lambda execution roles
# https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
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
  # https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
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
    path = var.lwf_path
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

############## Bastion host ##########################
# Bastion host in the EFS's VPC to get access to the EFS from local machine
# We need this access to copy the csv files

# Create a security group for the bastion host with SSH access from my local IP
resource "aws_security_group" "bastion_sg" {
  name_prefix = "bastion-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["147.12.250.110/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }  
}

# Create the EC2 instance for the bastion host
resource "aws_instance" "bastion_host" {
  # Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
  ami           = "ami-01dd271720c1ba44f"
  instance_type = "t2.nano"

  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.bastion_sg.id]

  subnet_id = aws_subnet.lambda_subnet1.id
  associate_public_ip_address = true

  # User data script to set up the bastion host
  # https://github.com/aws/efs-utils
  user_data = <<-EOT
    #!/bin/bash
    # Downloading EFS mount helper, https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-mount-helper-ec2-linux.html
    mkdir ${var.bastion_mount_path_to_lwf}
    sudo mkdir ${var.bastion_mount_path_to_root}
    sudo apt-get update
    sudo apt-get -y install nfs-common  

    sudo apt-get -y install git binutils
    git clone https://github.com/aws/efs-utils
    cd efs-utils
    ./build-deb.sh
    sudo apt-get -y install ./build/amazon-efs-utils*deb

    sudo mount -t efs ${aws_efs_file_system.roboclimate.id}:/ ${var.bastion_mount_path_to_root}
    sudo mount -t efs -o tls,accesspoint=${aws_efs_access_point.roboclimate.id} ${aws_efs_file_system.roboclimate.id}:/ ${var.bastion_mount_path_to_lwf}
    # Update /etc/fstab for Automatic Mounting: To ensure the EFS file system is mounted automatically on boot, 
    # add an entry to the /etc/fstab file
    echo "${aws_efs_file_system.roboclimate.id}:/ ${var.bastion_mount_path_to_root} efs defaults 0 0" | sudo tee -a /etc/fstab
    echo "${aws_efs_file_system.roboclimate.id}:/ ${var.bastion_mount_path_to_lwf} efs _netdev,tls,accesspoint=${aws_efs_access_point.roboclimate.id} 0 0" | sudo tee -a /etc/fstab
    echo "Bastion host setup complete."
  EOT


  tags = {
    Name = "Bastion Host"    
  }
}
