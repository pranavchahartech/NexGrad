data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}

# ==============================================================================
# EC2-1: NexGrad Frontend (Nginx Reverse Proxy & Static Asset Caching)
# ==============================================================================
resource "aws_instance" "frontend" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = var.public_subnet_id
  vpc_security_group_ids      = [var.frontend_sg_id]
  iam_instance_profile        = var.target_profile_name
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y git curl openssh-server
              systemctl enable --now ssh
              systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service || systemctl enable amazon-ssm-agent
              systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service || systemctl start amazon-ssm-agent
              echo "NexGrad Frontend Initialized" > /var/log/nexgrad-init.log
              EOF

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend"
    Role = "Frontend"
  }
}

# ==============================================================================
# EC2-2: NexGrad Backend (Django, Gemini API, On-Instance PostgreSQL)
# ==============================================================================
resource "aws_instance" "backend" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = var.backend_subnet_id
  vpc_security_group_ids      = [var.backend_sg_id]
  iam_instance_profile        = var.target_profile_name
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y git curl openssh-server
              systemctl enable --now ssh
              systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service || systemctl enable amazon-ssm-agent
              systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service || systemctl start amazon-ssm-agent
              echo "NexGrad Backend Initialized" > /var/log/nexgrad-init.log
              EOF

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
    Role = "Backend"
  }
}

# ==============================================================================
# EC2-3: DevOps Management (Ansible Controller, Puppet Server, Nagios Core)
# ==============================================================================
resource "aws_instance" "management" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = var.management_subnet_id
  vpc_security_group_ids      = [var.management_sg_id]
  iam_instance_profile        = var.management_profile_name
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y git curl openssh-server python3 python3-pip python3-venv unzip
              systemctl enable --now ssh

              # Install AWS CLI v2
              curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
              unzip -q /tmp/awscliv2.zip -d /tmp
              /tmp/aws/install

              # Install AWS Session Manager Plugin for SSM proxying
              curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "/tmp/session-manager-plugin.deb"
              dpkg -i /tmp/session-manager-plugin.deb

              # Install Ansible and AWS Python SDK
              apt-get install -y ansible
              pip3 install --no-cache-dir boto3 botocore

              # Install Ansible collections
              ansible-galaxy collection install ansible.posix community.aws amazon.aws community.postgresql

              echo "NexGrad Management Controller Initialized" > /var/log/nexgrad-init.log
              EOF

  tags = {
    Name = "${var.project_name}-${var.environment}-management"
    Role = "Management"
  }
}
