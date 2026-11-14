#!/bin/bash
# Rolling update with serial node execution to guarantee zero downtime
echo "Executing rolling update with Ansible..."
ansible-playbook -i ansible/inventory/hosts.ini ansible/playbooks/deploy.yml --extra-vars "serial_count=1"

