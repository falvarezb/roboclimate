# https://docs.aws.amazon.com/lambda/latest/dg/welcome.html

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      app = "t_roboclimate"
    }
  }

}

############## Lambda functions ##########################

module "weather_function" {
  source = "./modules/lambda"

  function_name = "t_roboclimate_weather"
  handler_name       = "weather_spider_lambda.weather_handler"
  execution_role = aws_iam_role.main_lambda_exec.arn
  subnet_ids         = [module.efs.lambda_subnet1_id, module.efs.lambda_subnet2_id]
  security_group_ids = [module.efs.efs_mount_target_sg_id]
  access_point_arn = module.efs.access_point_arn
  artifact_folder = "weather_spider_pkg"
  open_weather_api = var.open_weather_api
  s3_bucket_name = ""
  
  # Explicitly declare dependency on EFS mount target.
  # When creating or updating Lambda functions, mount target must be in 'available' lifecycle state.
  depends_on = [module.efs]
}

module "forecast_function" {
  source = "./modules/lambda"

  function_name = "t_roboclimate_forecast"
  handler_name       = "forecast_spider_lambda.forecast_handler"
  execution_role = aws_iam_role.main_lambda_exec.arn
  subnet_ids         = [module.efs.lambda_subnet1_id, module.efs.lambda_subnet2_id]
  security_group_ids = [module.efs.efs_mount_target_sg_id]
  access_point_arn = module.efs.access_point_arn
  artifact_folder = "forecast_spider_pkg"
  open_weather_api = var.open_weather_api
  s3_bucket_name = ""

  # Explicitly declare dependency on EFS mount target.
  # When creating or updating Lambda functions, mount target must be in 'available' lifecycle state.
  depends_on = [module.efs]
}

module "uvi_function" {
  source = "./modules/lambda"

  function_name = "t_roboclimate_uvi"
  handler_name       = "uvi_spider_lambda.handler"
  execution_role = aws_iam_role.main_lambda_exec.arn
  subnet_ids         = [module.efs.lambda_subnet1_id, module.efs.lambda_subnet2_id]
  security_group_ids = [module.efs.efs_mount_target_sg_id]
  access_point_arn = module.efs.access_point_arn
  artifact_folder = "uvi_spider_pkg"
  open_weather_api = var.open_weather_api
  s3_bucket_name = ""

  # Explicitly declare dependency on EFS mount target.
  # When creating or updating Lambda functions, mount target must be in 'available' lifecycle state.
  depends_on = [module.efs]
}

module "backup_function" {
  source = "./modules/lambda"

  function_name = "t_roboclimate_backup"
  handler_name       = "backup_lambda.handler"
  execution_role = aws_iam_role.backup_lambda_exec.arn
  subnet_ids         = [module.efs.lambda_subnet1_id, module.efs.lambda_subnet2_id]
  security_group_ids = [module.efs.efs_mount_target_sg_id]
  access_point_arn = module.efs.access_point_arn
  artifact_folder = "backup_pkg"
  open_weather_api = ""
  s3_bucket_name = var.s3_bucket

  # Explicitly declare dependency on EFS mount target.
  # When creating or updating Lambda functions, mount target must be in 'available' lifecycle state.
  depends_on = [module.efs]
}


# Lambda execution roles
# https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
resource "aws_iam_role" "main_lambda_exec" {
  # Main role used by lambda functions to execute
  name = "t_main_roboclimate_role"

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

resource "aws_iam_role" "backup_lambda_exec" {
  # Like the main role but authorised to access S3 bucket 'roboclimate' to back up EFS's csv files
  # Authorisation is managed by a resource-based policy attached to the bucket
  name = "t_s3_bucket_roboclimate_role"

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

resource "aws_iam_role_policy_attachment" "lambda_policy1" {
  role       = aws_iam_role.main_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaExecute"
}

resource "aws_iam_role_policy_attachment" "lambda_eni_policy1" {
  # https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
  # policy to create and manage ENIs (Elastic Network Interfaces)
  role       = aws_iam_role.main_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_policy2" {
  role       = aws_iam_role.backup_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambdaExecute"
}

resource "aws_iam_role_policy_attachment" "lambda_eni_policy2" {
  # https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
  # policy to create and manage ENIs (Elastic Network Interfaces)
  role       = aws_iam_role.backup_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}


############## Elastic File System ##########################

#This uses the default VPC.  It WILL NOT delete it on destroy.
resource "aws_default_vpc" "default" {
}

module "efs" {
  source = "./modules/efs"

  lambda_cidr_subnet1 = var.lambda_cidr_subnet1
  lambda_cidr_subnet2 = var.lambda_cidr_subnet2
  lambda_az1 = var.lambda_az1
  lambda_az2 = var.lambda_az2
  lwf_path = var.lwf_path
}


# Add a route table to route traffic from private subnets to NAT instance
resource "aws_route_table" "lambda_subnet" {
  vpc_id = aws_default_vpc.default.id

  route {
    cidr_block  = "0.0.0.0/0"
    instance_id = aws_instance.nat_instance.id
  }

  tags = {
    Name = "roboclimate"
  }
}

resource "aws_route_table_association" "lambda_subnet1" {
  subnet_id      = module.efs.lambda_subnet1_id
  route_table_id = aws_route_table.lambda_subnet.id
}

# This association may incur extra costs as it enables traffic between different availability zones
resource "aws_route_table_association" "lambda_subnet2" {
  subnet_id      = module.efs.lambda_subnet2_id
  route_table_id = aws_route_table.lambda_subnet.id
}


############## NAT instance ##########################
# NAT instance to allow lambda function access to the Internet
# https://docs.aws.amazon.com/vpc/latest/userguide/VPC_NAT_Instance.html

# It also plays role of bastion host to access private resources like the EFS

# Create a public subnet to host the NAT instance
resource "aws_subnet" "nat_subnet" {
  vpc_id                  = aws_default_vpc.default.id
  cidr_block              = var.nat_cidr_subnet
  availability_zone       = var.lambda_az1
  map_public_ip_on_launch = true

  tags = {
    Name = "roboclimate nat"
  }
}


# Create a security group for the NAT instance
resource "aws_security_group" "nat_sg" {
  name_prefix = "nat-instance-sg-"
  vpc_id      = aws_default_vpc.default.id

  # rules to allow lambda functions and EFS instance access to the internet
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.lambda_cidr_subnet1, var.lambda_cidr_subnet2]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # allow ssh access from my local IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  tags = {
    Name = "roboclimate nat"
  }
}

# Create the NAT instance
resource "aws_instance" "nat_instance" {
  # Amazon Linux: amzn-ami-vpc-nat-2018.03.0.20230724.0-x86_64-ebs
  ami           = "ami-091846419ebe1075b"
  instance_type = "t2.nano"

  key_name               = var.ssh_key_name
  vpc_security_group_ids = [aws_security_group.nat_sg.id]

  subnet_id                   = aws_subnet.nat_subnet.id
  associate_public_ip_address = true
  source_dest_check           = false

  tags = {
    Name = "roboclimate nat"
  }
}

############## EFS instance ##########################
# EC2 instance to get access to the EFS
# It must sit in a subnet with an EFS mount target
# We need this access to be able to upload/download the csv files used by the lambda functions

resource "aws_security_group" "efs_instance_sg" {
  name_prefix = "efs-instance-sg-"

  # ssh access allowed from NAT subnet only
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.nat_cidr_subnet]
  }

  # allow all access to the internet (needed to install efs-utils) 
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "roboclimate efs instance"
  }
}

resource "aws_instance" "efs_instance" {
  # Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
  ami           = "ami-01dd271720c1ba44f"
  instance_type = "t2.nano"

  key_name               = var.ssh_key_name
  vpc_security_group_ids = [aws_security_group.efs_instance_sg.id]

  # same subnet as one of the efs mount targets
  subnet_id                   = module.efs.lambda_subnet1_id
  associate_public_ip_address = false

  # User data script to set up efs utils (https://github.com/aws/efs-utils)
  user_data = <<-EOT
    #!/bin/bash
    set -ex
    # Create local folders to mount different paths of the EFS filesystem
    mkdir -p ${var.mount_path_to_lwf}
    chown -R ubuntu:ubuntu ${var.mount_path_to_lwf}
    mkdir -p ${var.mount_path_to_root}    
    chown -R ubuntu:ubuntu ${var.mount_path_to_root}

    # Downloading EFS mount helper, https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-mount-helper-ec2-linux.html
    apt-get update
    apt-get -y install nfs-common  

    apt-get -y install git binutils
    git clone https://github.com/aws/efs-utils
    cd efs-utils
    ./build-deb.sh
    apt-get -y install ./build/amazon-efs-utils*deb

    mount -t efs ${module.efs.file_system_id}:/ ${var.mount_path_to_root}
    mount -t efs -o tls,accesspoint=${module.efs.access_point_id} ${module.efs.file_system_id}:/ ${var.mount_path_to_lwf}
    # Update /etc/fstab for Automatic Mounting: To ensure the EFS file system is mounted automatically on boot, 
    # add an entry to the /etc/fstab file
    echo "${module.efs.file_system_id} ${var.mount_path_to_root} efs _netdev,tls,nofail 0 0" | sudo tee -a /etc/fstab
    echo "${module.efs.file_system_id} ${var.mount_path_to_lwf} efs _netdev,tls,accesspoint=${module.efs.access_point_id},nofail 0 0" | sudo tee -a /etc/fstab
    echo "EFS instance setup complete."
  EOT


  tags = {
    Name = "roboclimate efs"
  }
}

############## Lambda execution scheduler ##########################
module "eventbridge_scheduler" {
  source = "./modules/eventbridge"

  weather_lambda_arn = "${module.weather_function.function_arn}:23"
  forecast_lambda_arn = "${module.forecast_function.function_arn}:8"
  uvi_lambda_arn = "${module.uvi_function.function_arn}:4"
  backup_lambda_arn = "${module.backup_function.function_arn}:1"
}


############## S3 bucket ##########################
resource "aws_s3_bucket" "roboclimate" {
  bucket = var.s3_bucket
  
}

# Policy to allow the backup lambda function to access the S3 bucket
resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.roboclimate.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account}:role/${aws_iam_role.backup_lambda_exec.name}"
        },
        Action = [          
          "s3:PutObject"          
        ],
        Resource = "${aws_s3_bucket.roboclimate.arn}/*"
      }
    ]
  })
}