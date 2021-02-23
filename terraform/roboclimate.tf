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
variable "blue_instance" {}
variable "green_instance" {}


variable "enable_blue_application" {
  default = false
  type    = bool
}

variable "enable_green_application" {
  default = true
  type    = bool
}

variable "default_tags" { 
    type = map(string) 
    default = { 
        "Name": "roboclimate"
  } 
}

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
}

##################################################################################
# RESOURCES
##################################################################################

#This uses the default VPC.  It WILL NOT delete it on destroy.
resource "aws_default_vpc" "default" {

}

resource "aws_security_group" "roboclimate_blue" {
  count       = var.enable_blue_application ? 1 : 0
  name        = "roboclimate_blue"
  description = "Allow ssh and web access"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(map("color","blue"), var.default_tags)
}

resource "aws_instance" "roboclimate_blue" {
  count                  = var.enable_blue_application ? 1 : 0
  ami                    = "ami-018d4e875cb0a2a67"
  instance_type          = "t2.nano"
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.roboclimate_blue.0.id]

  connection {
    type        = "ssh"
    host        = self.public_ip
    user        = "ec2-user"
    private_key = file(var.private_key_path)

  }

  provisioner "local-exec" {
    command = "echo \"ssh-keyscan -H ${aws_instance.roboclimate_blue.0.public_dns} >> ~/.ssh/known_hosts\" > copy_csv_files.sh"
  }

  provisioner "local-exec" {
    command ="echo \"scp -3 -i ${var.private_key_path} -r ec2-user@${var.green_instance}:~/csv_files ec2-user@${aws_instance.roboclimate_blue.0.public_dns}:~/\" >> copy_csv_files.sh"    
  }

  provisioner "local-exec" {
    command ="chmod +x copy_csv_files.sh"    
  }

  provisioner "file" {
    source      = "../roboclimate"
    destination = "/home/ec2-user"
  }

  provisioner "file" {
    source      = "../notebook.ipynb"
    destination = "/home/ec2-user/notebook.ipynb"
  }

  provisioner "file" {
    source      = "../nbconverter.sh"
    destination = "/home/ec2-user/nbconverter.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo yum -y update",
      "sudo yum -y install tmux",
      "conda install -c conda-forge -y apscheduler", 
      "echo 'export PYTHONPATH=/home/ec2-user' >> /home/ec2-user/.bash_profile",
      "echo \"export OPEN_WEATHER_API=${var.open_weather_api}\" >> /home/ec2-user/.bash_profile",
      "sudo yum install nginx -y",
      "sudo service nginx start",
      "chmod u+x /home/ec2-user/nbconverter.sh",
      "sudo mkdir /usr/share/nginx/html/roboclimate",
      "sudo chown ec2-user /usr/share/nginx/html/roboclimate"            
    ]
  }


  tags = merge(map("color","blue"), var.default_tags)
}

resource "aws_security_group" "roboclimate_green" {
  count       = var.enable_green_application ? 1 : 0
  // name        = "roboclimate_green"
  description = "Allow ssh access"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(map("color","green"), var.default_tags)
}

resource "aws_instance" "roboclimate_green" {
  count                  = var.enable_green_application ? 1 : 0
  ami                    = "ami-018d4e875cb0a2a67"
  instance_type          = "t2.nano"
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.roboclimate_green.0.id]

  connection {
    type        = "ssh"
    host        = self.public_ip
    user        = "ec2-user"
    private_key = file(var.private_key_path)

  }

  provisioner "local-exec" {
    command = "echo \"ssh-keyscan -H ${aws_instance.roboclimate_green.0.public_dns} >> ~/.ssh/known_hosts\" > copy_csv_files.sh"
  }

  provisioner "local-exec" {
    command ="echo \"scp -3 -i ${var.private_key_path} -r ec2-user@${var.blue_instance}:~/csv_files ec2-user@${aws_instance.roboclimate_green.0.public_dns}:~/\" >> copy_csv_files.sh"    
  }

  provisioner "local-exec" {
    command ="chmod +x copy_csv_files.sh"    
  }

  provisioner "file" {
    source      = "../roboclimate"
    destination = "/home/ec2-user"
  }

  provisioner "file" {
    source      = "../notebook.ipynb"
    destination = "/home/ec2-user/notebook.ipynb"
  }

  provisioner "file" {
    source      = "../nbconverter.sh"
    destination = "/home/ec2-user/nbconverter.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo yum -y update",
      "sudo yum -y install tmux",
      "conda install -c conda-forge -y apscheduler", 
      "echo 'export PYTHONPATH=/home/ec2-user' >> /home/ec2-user/.bash_profile",
      "echo \"export OPEN_WEATHER_API=${var.open_weather_api}\" >> /home/ec2-user/.bash_profile",
      "sudo yum install nginx -y",
      "sudo service nginx start",
      "chmod u+x /home/ec2-user/nbconverter.sh",
      "sudo mkdir /usr/share/nginx/html/roboclimate",
      "sudo chown ec2-user /usr/share/nginx/html/roboclimate"             
    ]
  }


  tags = merge(map("color","green"), var.default_tags)
}

##################################################################################
# OUTPUT
##################################################################################

output "aws_instance_public_dns_blue" {
  value = [aws_instance.roboclimate_blue.*.public_dns]
}

output "aws_instance_public_dns_green" {
  value = [aws_instance.roboclimate_green.*.public_dns]
}
