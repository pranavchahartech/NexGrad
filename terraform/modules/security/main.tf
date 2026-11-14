# ==============================================================================
# NexGrad Security Groups (Zero Inbound Port 22 - Controlled via AWS SSM)
# Uses standalone aws_security_group_rule to prevent circular SG dependencies
# ==============================================================================

# 1. Frontend Security Group (EC2-1: Nginx)
resource "aws_security_group" "frontend" {
  name        = "${var.project_name}-${var.environment}-frontend-sg"
  description = "Allows public web traffic to Nginx and internal monitoring"
  vpc_id      = var.vpc_id

  ingress {
    description = "Public HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Public HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic for SSM agent, updates, and inter-service proxying"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-frontend-sg"
    Role = "Frontend"
  }
}

# 2. Backend Security Group (EC2-2: Django + On-Instance PostgreSQL)
resource "aws_security_group" "backend" {
  name        = "${var.project_name}-${var.environment}-backend-sg"
  description = "Allows traffic from Frontend and Management; PostgreSQL is local (127.0.0.1)"
  vpc_id      = var.vpc_id

  egress {
    description = "All outbound traffic for Gemini API, SSM agent, and Puppet agent"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-sg"
    Role = "Backend"
  }
}

# 3. Management Security Group (EC2-3: Ansible, Puppet Server, Nagios)
resource "aws_security_group" "management" {
  name        = "${var.project_name}-${var.environment}-management-sg"
  description = "Allows Puppet agent ingress on 8140 and admin Nagios dashboard access"
  vpc_id      = var.vpc_id

  ingress {
    description = "Nagios Web UI access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    description = "All outbound traffic for Ansible SSM sessions, Nagios probes, and updates"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-management-sg"
    Role = "Management"
  }
}

# ==============================================================================
# Cross-Group Rules (Defined via aws_security_group_rule to eliminate cycles)
# ==============================================================================

# Frontend Ingress: Nagios NRPE from Management
resource "aws_security_group_rule" "frontend_from_mgmt_nrpe" {
  type                     = "ingress"
  description              = "Nagios NRPE monitoring from Management"
  from_port                = 5666
  to_port                  = 5666
  protocol                 = "tcp"
  security_group_id        = aws_security_group.frontend.id
  source_security_group_id = aws_security_group.management.id
}

# Backend Ingress: Django Gunicorn from Frontend
resource "aws_security_group_rule" "backend_from_frontend_django" {
  type                     = "ingress"
  description              = "Django Gunicorn proxy from Frontend Nginx"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  security_group_id        = aws_security_group.backend.id
  source_security_group_id = aws_security_group.frontend.id
}

# Backend Ingress: Health check from Management Nagios
resource "aws_security_group_rule" "backend_from_mgmt_health" {
  type                     = "ingress"
  description              = "Nagios HTTP health check from Management"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  security_group_id        = aws_security_group.backend.id
  source_security_group_id = aws_security_group.management.id
}

# Backend Ingress: Nagios NRPE from Management
resource "aws_security_group_rule" "backend_from_mgmt_nrpe" {
  type                     = "ingress"
  description              = "Nagios NRPE monitoring from Management"
  from_port                = 5666
  to_port                  = 5666
  protocol                 = "tcp"
  security_group_id        = aws_security_group.backend.id
  source_security_group_id = aws_security_group.management.id
}

# Management Ingress: Puppet agent from Frontend
resource "aws_security_group_rule" "mgmt_from_frontend_puppet" {
  type                     = "ingress"
  description              = "Puppet Agent communication from Frontend"
  from_port                = 8140
  to_port                  = 8140
  protocol                 = "tcp"
  security_group_id        = aws_security_group.management.id
  source_security_group_id = aws_security_group.frontend.id
}

# Management Ingress: Puppet agent from Backend
resource "aws_security_group_rule" "mgmt_from_backend_puppet" {
  type                     = "ingress"
  description              = "Puppet Agent communication from Backend"
  from_port                = 8140
  to_port                  = 8140
  protocol                 = "tcp"
  security_group_id        = aws_security_group.management.id
  source_security_group_id = aws_security_group.backend.id
}
