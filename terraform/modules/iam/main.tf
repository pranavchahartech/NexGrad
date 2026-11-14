data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ==============================================================================
# 1. Target Instances IAM Role & Profile (EC2-1: Frontend, EC2-2: Backend)
# Provides baseline permissions for SSM Agent to establish outbound connectivity
# ==============================================================================
resource "aws_iam_role" "target_ssm_role" {
  name = "${var.project_name}-${var.environment}-target-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-target-ssm-role"
  }
}

resource "aws_iam_role_policy_attachment" "target_ssm_core" {
  role       = aws_iam_role.target_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "target_profile" {
  name = "${var.project_name}-${var.environment}-target-ssm-profile"
  role = aws_iam_role.target_ssm_role.name
}

# ==============================================================================
# 2. Management Controller IAM Role & Profile (EC2-3: Ansible Controller)
# Authorizes Ansible to discover instances, initiate SSM sessions, & run commands
# ==============================================================================
resource "aws_iam_role" "management_ssm_role" {
  name = "${var.project_name}-${var.environment}-mgmt-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-mgmt-ssm-role"
  }
}

resource "aws_iam_role_policy_attachment" "mgmt_ssm_core" {
  role       = aws_iam_role.management_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_policy" "mgmt_session_starter" {
  name        = "${var.project_name}-${var.environment}-ssm-initiator-policy"
  description = "Allows Ansible on EC2-3 to manage SSM sessions and run commands on target instances"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SSMInstanceDiscovery"
        Effect = "Allow"
        Action = [
          "ssm:DescribeInstanceInformation",
          "ssm:GetConnectionStatus",
          "ssm:DescribeSessions",
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Sid    = "SSMSessionManagement"
        Effect = "Allow"
        Action = [
          "ssm:StartSession",
          "ssm:TerminateSession",
          "ssm:ResumeSession"
        ]
        Resource = [
          "arn:aws:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:instance/*"
        ]
      },
      {
        Sid    = "SSMDocumentAccess"
        Effect = "Allow"
        Action = [
          "ssm:GetDocument",
          "ssm:DescribeDocument"
        ]
        Resource = [
          "arn:aws:ssm:*:*:document/SSM-SessionManagerRunShell",
          "arn:aws:ssm:*:*:document/AWS-StartSSHSession",
          "arn:aws:ssm:*:*:document/AWS-RunShellScript"
        ]
      },
      {
        Sid    = "SSMCommandExecution"
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:ListCommands",
          "ssm:ListCommandInvocations",
          "ssm:GetCommandInvocation"
        ]
        Resource = [
          "arn:aws:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:instance/*",
          "arn:aws:ssm:*:*:document/AWS-RunShellScript"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "mgmt_session_attach" {
  role       = aws_iam_role.management_ssm_role.name
  policy_arn = aws_iam_policy.mgmt_session_starter.arn
}

resource "aws_iam_instance_profile" "management_profile" {
  name = "${var.project_name}-${var.environment}-mgmt-ssm-profile"
  role = aws_iam_role.management_ssm_role.name
}

