##################################################################################
# VARIABLES
##################################################################################

variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "aws_token" {}
variable "private_key_path" {}
variable "key_name" {}
variable "region" {
  default = "eu-west-1"
}
variable "open_weather_api" {}

##################################################################################
# PROVIDERS
##################################################################################

provider "aws" {
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  token = var.aws_token  
  region = var.region
}
##################################################################################
# LOCALS
##################################################################################

locals {
  common_tags = {
    Name = "roboclimate"     
  }
}

##################################################################################
# RESOURCES
##################################################################################

#This uses the default VPC.  It WILL NOT delete it on destroy.
resource "aws_default_vpc" "default" {

}

resource "aws_security_group" "roboclimate" {
  name        = "roboclimate"
  description = "Allow ssh access"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}


resource "aws_instance" "roboclimate" {
  ami                    = "ami-018d4e875cb0a2a67"
  instance_type          = "t2.nano"
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.roboclimate.id]

  connection {
    type        = "ssh"
    host        = self.public_ip
    user        = "ec2-user"
    private_key = file(var.private_key_path)

  }

  provisioner "remote-exec" {
    inline = [
      "sudo yum -y update",
      "sudo yum -y install tmux",
      "conda install -c conda-forge -y apscheduler", 
      "echo 'export PYTHONPATH=/home/ec2-user' >> /home/ec2-user/.bash_profile",
      "echo \"export OPEN_WEATHER_API=${var.open_weather_api}\" >> /home/ec2-user/.bash_profile"      
    ]
  }

  provisioner "file" {
    source      = "../roboclimate"
    destination = "/home/ec2-user"
  }

  tags = local.common_tags
}

##################################################################################
# OUTPUT
##################################################################################

output "aws_instance_public_dns" {
  value = aws_instance.roboclimate.public_dns
}
