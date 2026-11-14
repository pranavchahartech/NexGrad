#!/bin/bash
# ==============================================================================
# Full Multi-Tier Automated Deployment Script
# Orchestrates Ansible and updates services across web, app, and AI tiers
# ==============================================================================

set -e
echo "Starting automated deployment across all production nodes..."

ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/site.yml
ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/deploy.yml

echo "Deployment complete! Running health checks..."
bash scripts/monitoring/health_check.sh

