# NexGrad Deployment Guide

## Prerequisites

- AWS CLI configured with administrator or deployer IAM privileges.
- Terraform >= 1.5.0
- Ansible >= 2.15.0
- Python >= 3.12

## Step-by-Step Deployment

### 1. Infrastructure Provisioning (Terraform)

```bash
cd terraform/environments/production
cp terraform.tfvars.example terraform.tfvars
# Update credentials and variables in terraform.tfvars
terraform init
terraform plan -out=tfplan
# Apply only when authorized:
# terraform apply tfplan
```

### 2. Configuration Management (Puppet / Ansible)

```bash
cd ../../../ansible
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

### 3. Application Deployment

```bash
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml
```

### 4. Verification

```bash
bash scripts/monitoring/health_check.sh <ALB_DNS_NAME>
```

