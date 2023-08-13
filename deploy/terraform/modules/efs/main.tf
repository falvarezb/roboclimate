############## Elastic File System ##########################

#This uses the default VPC.  It WILL NOT delete it on destroy.
resource "aws_default_vpc" "default" {
}

# Create access to the EFS through two private subnets in two different AZs for redundancy
resource "aws_subnet" "lambda_subnet1" {
  vpc_id                  = aws_default_vpc.default.id
  cidr_block              = var.lambda_cidr_subnet1
  availability_zone       = var.lambda_az1
  map_public_ip_on_launch = false

  tags = {
    Name = "roboclimate lambda1"
  }
}

resource "aws_subnet" "lambda_subnet2" {
  vpc_id                  = aws_default_vpc.default.id
  cidr_block              = var.lambda_cidr_subnet2
  availability_zone       = var.lambda_az2
  map_public_ip_on_launch = false

  tags = {
    Name = "roboclimate lambda2"
  }
}


# Create a security group for the EFS mount target
resource "aws_security_group" "efs_mount_target_sg" {
  name_prefix = "roboclimate-efs-mount-target-sg-"

  vpc_id = aws_default_vpc.default.id

  # allow access to EFS's port 2049
  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = [var.lambda_cidr_subnet1, var.lambda_cidr_subnet2]
  }

  # allow all traffic from EFS
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "roboclimate efs"
  }
}

# Create an Elastic File System (EFS)
resource "aws_efs_file_system" "roboclimate" {
  creation_token = "roboclimate"

  tags = {
    Name = "roboclimate"
  }

}


# Create a mount target for each subnet in each AZ
resource "aws_efs_mount_target" "roboclimate_efs_mount_target1" {
  file_system_id  = aws_efs_file_system.roboclimate.id
  subnet_id       = aws_subnet.lambda_subnet1.id
  security_groups = [aws_security_group.efs_mount_target_sg.id]
}

resource "aws_efs_mount_target" "roboclimate_efs_mount_target2" {
  file_system_id  = aws_efs_file_system.roboclimate.id
  subnet_id       = aws_subnet.lambda_subnet2.id
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

  tags = {
    Name = "roboclimate"
  }
}