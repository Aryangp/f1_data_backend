terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  # Region picked up from AWS_REGION environment variable
}

# Dynamic AMI lookup for Ubuntu 22.04 (Works in any region)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ECR Repository
resource "aws_ecr_repository" "f1_app_repo" {
  name                 = "f1-race-backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

# Key Pair
resource "tls_private_key" "pk" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "kp" {
  key_name   = "f1-key"
  public_key = tls_private_key.pk.public_key_openssh
}

# Security Group
resource "aws_security_group" "f1_sg" {
  name        = "f1_security_group"
  description = "Allow inbound traffic for F1 App"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "f1_app_server" {
  ami           = data.aws_ami.ubuntu.id
  # t3.micro is Free Tier eligible in eu-north-1 (Stockholm) and most modern regions.
  # t2.micro is NOT available in eu-north-1.
  instance_type = "t3.micro" 
  key_name      = aws_key_pair.kp.key_name
  
  vpc_security_group_ids = [aws_security_group.f1_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update
              sudo apt-get install -y docker.io unzip
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -aG docker ubuntu
              
              # Install AWS CLI
              curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
              unzip awscliv2.zip
              sudo ./aws/install

              # Configure Swap (2GB) to prevent OOM
              sudo fallocate -l 2G /swapfile
              sudo chmod 600 /swapfile
              sudo mkswap /swapfile
              sudo swapon /swapfile
              echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
              EOF

  tags = {
    Name = "F1RaceBackend"
  }
}

# Elastic IP
resource "aws_eip" "f1_eip" {
  instance = aws_instance.f1_app_server.id
  domain   = "vpc"
}
